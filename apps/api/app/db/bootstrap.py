from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.models import blog_post, brand_profile, content_plan, job_run, monitoring, product, social_account, system  # noqa: F401


async def create_database_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

