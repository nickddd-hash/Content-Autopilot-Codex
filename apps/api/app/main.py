import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.db.bootstrap import create_database_tables
from app.db.session import AsyncSessionLocal, engine
from app.services.plan_execution import process_due_autopost_items


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(api_router, prefix=settings.api_prefix)

generated_media_dir = Path(settings.media_storage_dir)
generated_media_dir.mkdir(parents=True, exist_ok=True)
app.mount(f"{settings.api_prefix}/media", StaticFiles(directory=generated_media_dir), name="media")


async def _autopost_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as session:
                await process_due_autopost_items(session)
        except Exception:
            # Keep the scheduler alive even if one iteration fails.
            pass
        await asyncio.sleep(60)


@app.on_event("startup")
async def on_startup() -> None:
    if settings.auto_create_tables and settings.environment != "production":
        await create_database_tables(engine)
    app.state.autopost_task = asyncio.create_task(_autopost_loop())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    autopost_task = getattr(app.state, "autopost_task", None)
    if autopost_task is not None:
        autopost_task.cancel()
        try:
            await autopost_task
        except asyncio.CancelledError:
            pass


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Athena Content Autopilot API"}
