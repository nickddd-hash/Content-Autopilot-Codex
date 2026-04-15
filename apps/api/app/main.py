from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.bootstrap import create_database_tables
from app.db.session import engine


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def on_startup() -> None:
    if settings.auto_create_tables and settings.environment != "production":
        await create_database_tables(engine)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Athena Content Autopilot API"}
