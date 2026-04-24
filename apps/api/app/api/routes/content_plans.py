from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db_session
from app.models import ContentPlan, ContentPlanItem, Product
from app.schemas.content_plan import (
    PLAN_DIRECTION_KEYS,
    ArchivedContentItemRead,
    ContentPlanCreate,
    ContentPlanItemDetailRead,
    ContentPlanItemCreate,
    ContentPlanItemRead,
    ContentPlanItemStatusUpdate,
    ContentPlanItemUpdate,
    ContentPlanRead,
    ContentPlanUpdate,
    GeneratePlanItemsPayload,
    QuickPostPayload,
    RunPlanPipelinePayload,
)
from app.schemas.job_run import JobRunRead, StartGenerationResponse
from app.services.generation import build_content_plan_item_detail, start_manual_generation, validate_status_transition
from app.services.media_generator import generate_illustration_for_item, save_uploaded_illustration_for_item
from app.services.plan_execution import (
    build_plan_materials,
    get_latest_item_job,
    get_latest_plan_job,
    publish_plan_item_now,
    start_plan_pipeline_job,
)
from app.services.plan_generation import generate_plan_items_for_plan, generate_rewrite_items_from_ingested

router = APIRouter()
QUICK_POST_PLACEHOLDER_TITLE = "Пост по тезисам"


def _plan_query() -> object:
    return (
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .options(selectinload(ContentPlan.product))
        .order_by(ContentPlan.created_at.desc())
    )


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


def _build_archived_item(item: ContentPlanItem, plan: ContentPlan, product: Product) -> dict:
    generation_payload = item.research_data.get("generation_payload", {}) if isinstance(item.research_data, dict) else {}
    if not isinstance(generation_payload, dict):
        generation_payload = {}

    return {
        "id": item.id,
        "plan_id": plan.id,
        "product_id": product.id,
        "product_name": product.name,
        "plan_month": plan.month,
        "plan_theme": plan.theme,
        "title": item.title,
        "angle": item.angle,
        "article_type": item.article_type,
        "status": item.status,
        "target_keywords": item.target_keywords,
        "scheduled_at": item.scheduled_at,
        "published_at": item.published_at,
        "updated_at": item.updated_at,
        "generated_draft_title": generation_payload.get("draft_title"),
        "generated_draft_markdown": generation_payload.get("draft_markdown"),
    }


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


@router.get("/archive/items", response_model=list[ArchivedContentItemRead])
async def list_archived_content_items(
    product_id: UUID | None = None,
    query: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    statement = (
        select(ContentPlanItem, ContentPlan, Product)
        .join(ContentPlan, ContentPlan.id == ContentPlanItem.plan_id)
        .join(Product, Product.id == ContentPlan.product_id)
        .where(ContentPlanItem.status.in_(("archived", "published")))
        .order_by(ContentPlanItem.updated_at.desc())
    )
    if product_id is not None:
        statement = statement.where(ContentPlan.product_id == product_id)

    result = await session.execute(statement)
    records = result.all()
    normalized_query = (query or "").strip().lower()
    items: list[dict] = []

    for item, plan, product in records:
        archived_item = _build_archived_item(item, plan, product)
        if normalized_query:
            haystack = " ".join(
                filter(
                    None,
                    [
                        archived_item["product_name"],
                        archived_item["plan_month"],
                        archived_item["plan_theme"],
                        archived_item["title"],
                        archived_item["angle"] or "",
                        " ".join(archived_item["target_keywords"]),
                        archived_item["generated_draft_title"] or "",
                        archived_item["generated_draft_markdown"] or "",
                    ],
                )
            ).lower()
            if normalized_query not in haystack:
                continue

        items.append(archived_item)

    return items


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
        settings_json=payload.settings_json.model_dump(),
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


@router.get("/{plan_id}/latest-job", response_model=JobRunRead | None)
async def get_content_plan_latest_job(
    plan_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> JobRunRead | None:
    await _get_plan_or_404(session, plan_id)
    return await get_latest_plan_job(session, plan_id)


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
        if field_name == "settings_json" and hasattr(value, "model_dump"):
            value = value.model_dump()
        setattr(plan, field_name, value)
    await session.commit()
    return await _get_plan_or_404(session, plan_id)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_plan(
    plan_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    plan = await _get_plan_or_404(session, plan_id)
    await session.delete(plan)
    await session.commit()


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


@router.post("/{plan_id}/quick-post", response_model=ContentPlanItemDetailRead, status_code=status.HTTP_201_CREATED)
async def create_quick_post(
    plan_id: UUID,
    payload: QuickPostPayload,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    plan = await _get_plan_or_404(session, plan_id)
    existing_orders = [item.order for item in plan.items]
    next_order = (max(existing_orders) + 1) if existing_orders else 0
    title = (payload.title or "").strip()
    text = payload.text.strip()
    content_direction = (payload.content_direction or "educational").strip().lower()
    if content_direction not in PLAN_DIRECTION_KEYS:
        content_direction = "educational"
    available_channels = [str(channel).strip() for channel in (plan.product.primary_channels or []) if str(channel).strip()]
    selected_channels = [channel for channel in payload.channel_targets if channel in available_channels]
    if not selected_channels:
        selected_channels = list(available_channels)

    item = ContentPlanItem(
        plan_id=plan_id,
        order=next_order,
        title=title or QUICK_POST_PLACEHOLDER_TITLE,
        angle=text[:1000],
        target_keywords=[],
        article_type=content_direction,
        cta_type="soft",
        status="planned",
        research_data={
            "manual_brief": text,
            "creation_mode": "quick_post",
            "content_direction": content_direction,
            "channel_targets": selected_channels,
            "include_illustration": payload.include_illustration,
        },
        article_review={
            "creation_mode": "quick_post",
        },
    )

    if title and not payload.generate_now:
        item.status = "draft"
        item.research_data = {
            **item.research_data,
            "generation_payload": {
                "draft_title": title,
                "draft_markdown": text,
            },
        }
        item.article_review = {
            **item.article_review,
            "generation_mode": "manual_written",
        }

    session.add(item)
    await session.commit()

    if payload.generate_now:
        await start_manual_generation(session, plan_id, item.id, notes="Quick post generation")
        item = await _get_item_or_404(session, plan_id, item.id)
        generation_payload = item.research_data.get("generation_payload", {}) if isinstance(item.research_data, dict) else {}
        generated_title = generation_payload.get("draft_title") if isinstance(generation_payload, dict) else None
        generated_summary = generation_payload.get("summary") if isinstance(generation_payload, dict) else None

        if isinstance(generated_title, str) and generated_title.strip() and item.title == QUICK_POST_PLACEHOLDER_TITLE:
            item.title = generated_title.strip()

        if isinstance(generated_summary, str) and generated_summary.strip() and not item.angle:
            item.angle = generated_summary.strip()[:1000]

        await session.commit()
        await session.refresh(item)
        if payload.include_illustration:
            await generate_illustration_for_item(session, item)
            item = await _get_item_or_404(session, plan_id, item.id)
        return build_content_plan_item_detail(item)

    if payload.include_illustration:
        await generate_illustration_for_item(session, item)
        item = await _get_item_or_404(session, plan_id, item.id)

    item = await _get_item_or_404(session, plan_id, item.id)
    return build_content_plan_item_detail(item)


@router.get("/{plan_id}/items/{item_id}", response_model=ContentPlanItemDetailRead)
async def get_content_plan_item(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    item = await _get_item_or_404(session, plan_id, item_id)
    return build_content_plan_item_detail(item)


@router.get("/{plan_id}/items/{item_id}/latest-job", response_model=JobRunRead | None)
async def get_content_plan_item_latest_job(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> JobRunRead | None:
    await _get_item_or_404(session, plan_id, item_id)
    return await get_latest_item_job(session, item_id)


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


@router.post("/{plan_id}/items/{item_id}/generate", response_model=StartGenerationResponse)
async def generate_content_plan_item(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> StartGenerationResponse:
    return await start_manual_generation(session, plan_id, item_id, notes="Triggered from content plan routes")


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


@router.post("/{plan_id}/items/{item_id}/publish", response_model=ContentPlanItemDetailRead)
async def publish_content_plan_item(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await publish_plan_item_now(session, plan_id, item_id)


@router.post("/{plan_id}/items/{item_id}/generate-illustration", response_model=ContentPlanItemDetailRead)
async def generate_content_plan_item_illustration(
    plan_id: UUID,
    item_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    item = await _get_item_or_404(session, plan_id, item_id)
    await generate_illustration_for_item(session, item)
    return build_content_plan_item_detail(item)


@router.post("/{plan_id}/items/{item_id}/upload-illustration", response_model=ContentPlanItemDetailRead)
async def upload_content_plan_item_illustration(
    plan_id: UUID,
    item_id: UUID,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    item = await _get_item_or_404(session, plan_id, item_id)
    file_bytes = await image.read()
    await save_uploaded_illustration_for_item(
        session,
        item,
        file_bytes=file_bytes,
        mime_type=image.content_type or "",
        original_file_name=image.filename,
    )
    return build_content_plan_item_detail(item)


@router.post("/{plan_id}/build-materials", response_model=list[ContentPlanItemDetailRead])
async def build_content_plan_materials(
    plan_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    return await build_plan_materials(session, plan_id)


@router.post("/{plan_id}/run-pipeline", response_model=JobRunRead)
async def run_content_plan_pipeline(
    plan_id: UUID,
    payload: RunPlanPipelinePayload | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> JobRunRead:
    options = payload or RunPlanPipelinePayload()
    return await start_plan_pipeline_job(
        session,
        plan_id,
        generate_items=options.generate_items,
        theme_override=options.theme,
        num_items_override=options.num_items,
    )


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
