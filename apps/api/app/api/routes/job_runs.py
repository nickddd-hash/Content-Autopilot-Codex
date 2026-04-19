from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import JobRun
from app.schemas.job_run import JobRunRead, StartGenerationPayload, StartGenerationResponse
from app.services.generation import start_manual_generation


router = APIRouter()


@router.get("", response_model=list[JobRunRead])
async def list_job_runs(
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> list[JobRun]:
    statement = select(JobRun).order_by(JobRun.created_at.desc()).limit(min(max(limit, 1), 100))
    result = await session.execute(statement)
    return list(result.scalars().all())

@router.get("/content-plans/{plan_id}/items/{item_id}/latest", response_model=JobRunRead | None)
async def get_latest_job_run_for_item(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> JobRun | None:
    statement = (
        select(JobRun)
        .where(JobRun.content_plan_item_id == item_id)
        .order_by(JobRun.created_at.desc())
        .limit(1)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


@router.post(
    "/content-plans/{plan_id}/items/{item_id}/start-generation",
    response_model=StartGenerationResponse,
)
async def start_generation_for_item(
    plan_id: UUID,
    item_id: UUID,
    payload: StartGenerationPayload,
    session: AsyncSession = Depends(get_db_session),
) -> StartGenerationResponse:
    return await start_manual_generation(session, plan_id, item_id, payload.notes)
