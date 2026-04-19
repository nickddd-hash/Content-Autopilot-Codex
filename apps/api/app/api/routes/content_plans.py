from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models import ContentPlan, ContentPlanItem, Product
from app.schemas.content_plan import (
    ContentPlanCreate,
    ContentPlanItemDetailRead,
    ContentPlanItemCreate,
    ContentPlanItemRead,
    ContentPlanItemStatusUpdate,
    ContentPlanItemUpdate,
    ContentPlanRead,
    ContentPlanUpdate,
    GeneratePlanItemsPayload,
)
from app.services.generation import build_content_plan_item_detail, validate_status_transition
from app.services.plan_generation import generate_plan_items_for_plan, generate_rewrite_items_from_ingested

router = APIRouter()


def _plan_query() -> object:
    return select(ContentPlan).options(selectinload(ContentPlan.items)).order_by(ContentPlan.created_at.desc())


async def _get_plan_or_404(session: AsyncSession, plan_id: UUID) -> ContentPlan:
    plan = await session.scalar(_plan_query().where(ContentPlan.id == plan_id))
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found.")
    return plan


async def _get_item_or_404(session: AsyncSession, plan_id: UUID, item_id: UUID) -> ContentPlanItem:
    statement = select(ContentPlanItem).where(
        ContentPlanItem.id == item_id,
        ContentPlanItem.plan_id == plan_id,
    )
    item = await session.scalar(statement)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan item not found.")
    return item


def _build_item(payload: ContentPlanItemCreate) -> ContentPlanItem:
    return ContentPlanItem(**payload.model_dump())


@router.get("", response_model=list[ContentPlanRead])
async def list_content_plans(
    product_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ContentPlan]:
    statement = _plan_query()
    if product_id is not None:
        statement = statement.where(ContentPlan.product_id == product_id)
    result = await session.execute(statement)
    return list(result.scalars().unique().all())


@router.post("", response_model=ContentPlanRead, status_code=status.HTTP_201_CREATED)
async def create_content_plan(
    payload: ContentPlanCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlan:
    product = await session.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    plan = ContentPlan(
        product_id=payload.product_id,
        month=payload.month,
        theme=(payload.theme or "").strip(),
        status=payload.status,
    )
    plan.items = [_build_item(item) for item in payload.items]
    session.add(plan)
    await session.commit()
    return await _get_plan_or_404(session, plan.id)


@router.get("/{plan_id}", response_model=ContentPlanRead)
async def get_content_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlan:
    return await _get_plan_or_404(session, plan_id)


@router.patch("/{plan_id}", response_model=ContentPlanRead)
async def update_content_plan(
    plan_id: UUID,
    payload: ContentPlanUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlan:
    plan = await _get_plan_or_404(session, plan_id)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name == "theme":
            value = (value or "").strip()
        setattr(plan, field_name, value)
    await session.commit()
    return await _get_plan_or_404(session, plan_id)


@router.post("/{plan_id}/items", response_model=ContentPlanItemRead, status_code=status.HTTP_201_CREATED)
async def create_content_plan_item(
    plan_id: UUID,
    payload: ContentPlanItemCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlanItem:
    await _get_plan_or_404(session, plan_id)
    item = _build_item(payload)
    item.plan_id = plan_id
    session.add(item)
    await session.commit()
    return await _get_item_or_404(session, plan_id, item.id)


@router.get("/{plan_id}/items/{item_id}", response_model=ContentPlanItemDetailRead)
async def get_content_plan_item(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    item = await _get_item_or_404(session, plan_id, item_id)
    return build_content_plan_item_detail(item)


@router.patch("/{plan_id}/items/{item_id}", response_model=ContentPlanItemRead)
async def update_content_plan_item(
    plan_id: UUID,
    item_id: UUID,
    payload: ContentPlanItemUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlanItem:
    item = await _get_item_or_404(session, plan_id, item_id)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field_name, value)
    await session.commit()
    return await _get_item_or_404(session, plan_id, item_id)


@router.post("/{plan_id}/items/{item_id}/status", response_model=ContentPlanItemDetailRead)
async def update_content_plan_item_status(
    plan_id: UUID,
    item_id: UUID,
    payload: ContentPlanItemStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    item = await _get_item_or_404(session, plan_id, item_id)
    validate_status_transition(item.status, payload.status)
    item.status = payload.status
    await session.commit()
    await session.refresh(item)
    return build_content_plan_item_detail(item)


@router.post("/{plan_id}/generate-items", response_model=list[ContentPlanItemRead])
async def generate_plan_items(
    plan_id: UUID,
    payload: GeneratePlanItemsPayload | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ContentPlanItem]:
    """Uses LLM to generate items for the given content plan."""
    return await generate_plan_items_for_plan(
        session,
        plan_id,
        theme_override=payload.theme if payload else None,
        num_items_override=payload.num_items if payload else None,
    )


class RewriteFromIngestedPayload(BaseModel):
    ingested_content_ids: list[UUID]


@router.post("/{plan_id}/rewrite-from-ingested", response_model=list[ContentPlanItemRead])
async def rewrite_items_from_ingested(
    plan_id: UUID,
    payload: RewriteFromIngestedPayload,
    session: AsyncSession = Depends(get_db_session),
) -> list[ContentPlanItem]:
    """Creates ContentPlanItems from viral IngestedContent in 'Rewrite' mode."""
    return await generate_rewrite_items_from_ingested(session, plan_id, payload.ingested_content_ids)
