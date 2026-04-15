from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import ContentPlan, ContentPlanItem, JobRun, Product, ProductContentSettings
from app.schemas.dashboard import DashboardSummary


router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_db_session),
) -> DashboardSummary:
    total_products = await session.scalar(select(func.count(Product.id))) or 0
    active_products = await session.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))) or 0
    autopilot_enabled_products = (
        await session.scalar(
            select(func.count(ProductContentSettings.id)).where(ProductContentSettings.autopilot_enabled.is_(True))
        )
        or 0
    )
    total_content_plans = await session.scalar(select(func.count(ContentPlan.id))) or 0
    planned_items = (
        await session.scalar(select(func.count(ContentPlanItem.id)).where(ContentPlanItem.status == "planned")) or 0
    )
    published_items = (
        await session.scalar(select(func.count(ContentPlanItem.id)).where(ContentPlanItem.status == "published")) or 0
    )
    failed_items = (
        await session.scalar(select(func.count(ContentPlanItem.id)).where(ContentPlanItem.status == "failed")) or 0
    )
    running_jobs = await session.scalar(select(func.count(JobRun.id)).where(JobRun.status == "running")) or 0

    return DashboardSummary(
        total_products=total_products,
        active_products=active_products,
        autopilot_enabled_products=autopilot_enabled_products,
        total_content_plans=total_content_plans,
        planned_items=planned_items,
        published_items=published_items,
        failed_items=failed_items,
        running_jobs=running_jobs,
    )

