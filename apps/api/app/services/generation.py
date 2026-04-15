from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BrandProfile, ContentPlan, ContentPlanItem, JobRun, Product
from app.schemas.job_run import StartGenerationResponse
from app.services.generation_prompt import build_generation_messages
from app.services.llm_client import LLMClientError, generate_json

ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"draft"},
    "draft": {"review-ready", "planned"},
    "review-ready": {"draft", "published", "failed"},
    "failed": {"planned", "draft"},
    "published": set(),
}


async def get_content_plan_item_or_404(
    session: AsyncSession,
    plan_id: UUID,
    item_id: UUID,
) -> tuple[ContentPlan, ContentPlanItem]:
    plan_statement = (
        select(ContentPlan)
        .where(ContentPlan.id == plan_id)
        .options(selectinload(ContentPlan.product))
    )
    plan = await session.scalar(plan_statement)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found.")

    item_statement = select(ContentPlanItem).where(
        ContentPlanItem.id == item_id,
        ContentPlanItem.plan_id == plan_id,
    )
    item = await session.scalar(item_statement)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan item not found.")

    return plan, item


def _build_fallback_generation_payload(item: ContentPlanItem, product: Product | None) -> dict[str, Any]:
    product_name = product.name if product else "Product"
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "generator_mode": "fallback_stub",
        "draft_title": item.title,
        "draft_markdown": (
            f"# {item.title}\n\n"
            f"## Почему эта тема важна\n\n"
            f"{item.angle or 'Эта тема помогает человеку разобраться в проблеме и увидеть следующий шаг.'}\n\n"
            "## Как объяснить это без информационного шума\n\n"
            "Нужно показать проблему спокойно, структурно и без перегруза советами. "
            "Материал должен соединять образовательную ценность и реальную полезность.\n\n"
            "## Какой следующий шаг дать читателю\n\n"
            "Дать один ясный практический шаг и мягко подвести к более персональному маршруту."
        ),
        "summary": f"Черновой fallback draft для {product_name}.",
        "hook": "Почему люди читают о проблеме много, но все равно не понимают, что делать дальше?",
        "cta": "Если хочется не еще один совет, а понятный персональный следующий шаг, стоит перейти к более системному формату сопровождения.",
        "repurposing": {
            "post": f"Короткий пост по теме: {item.title}",
            "carousel": [
                "Слайд 1: в чем боль и путаница",
                "Слайд 2: какой системный взгляд нужен",
                "Слайд 3: какой следующий шаг можно сделать",
            ],
            "reel_script": f"Короткий reel script по теме: {item.title}",
        },
        "review_notes": [
            "Нужна реальная LLM-генерация для более глубокого драфта.",
            "Нужна редакторская проверка после подключения production pipeline.",
        ],
    }


def build_content_plan_item_detail(item: ContentPlanItem) -> dict[str, Any]:
    generation_payload = {}
    if isinstance(item.research_data, dict):
        generation_payload = item.research_data.get("generation_payload", {})

    if not isinstance(generation_payload, dict):
        generation_payload = {}

    return {
        "id": item.id,
        "plan_id": item.plan_id,
        "order": item.order,
        "title": item.title,
        "angle": item.angle,
        "target_keywords": item.target_keywords,
        "article_type": item.article_type,
        "cta_type": item.cta_type,
        "status": item.status,
        "scheduled_at": item.scheduled_at,
        "published_at": item.published_at,
        "telegraph_url": item.telegraph_url,
        "research_data": item.research_data,
        "article_review": item.article_review,
        "error_message": item.error_message,
        "retry_count": item.retry_count,
        "vk_post_id": item.vk_post_id,
        "vk_posted_at": item.vk_posted_at,
        "vk_adaptation": item.vk_adaptation,
        "vk_carousel": item.vk_carousel,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "generated_draft_title": generation_payload.get("draft_title"),
        "generated_draft_markdown": generation_payload.get("draft_markdown"),
        "generated_summary": generation_payload.get("summary"),
        "generated_hook": generation_payload.get("hook"),
        "generated_cta": generation_payload.get("cta"),
        "generation_mode": item.article_review.get("generation_mode") if isinstance(item.article_review, dict) else None,
    }
 

def validate_status_transition(current_status: str, next_status: str) -> None:
    if current_status == next_status:
        return

    allowed = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid status transition: {current_status} -> {next_status}",
        )


async def start_manual_generation(
    session: AsyncSession,
    plan_id: UUID,
    item_id: UUID,
    notes: str | None = None,
) -> StartGenerationResponse:
    plan, item = await get_content_plan_item_or_404(session, plan_id, item_id)
    now = datetime.now(UTC)
    brand_profile = await session.scalar(select(BrandProfile).limit(1))

    job_run = JobRun(
        job_type="manual_generation",
        status="running",
        product_id=plan.product_id,
        content_plan_item_id=item.id,
        started_at=now,
        meta_json={
            "mode": "manual",
            "notes": notes,
            "plan_id": str(plan.id),
            "content_plan_item_id": str(item.id),
            "stage": "draft_bootstrap",
        },
    )
    session.add(job_run)
    await session.flush()

    try:
        messages = build_generation_messages(plan.product, brand_profile, plan, item)
        generation_payload = await generate_json(messages)
        result_mode = "llm_generated"
    except LLMClientError as exc:
        generation_payload = _build_fallback_generation_payload(item, plan.product)
        result_mode = "fallback_generated"
        job_run.meta_json = {
            **job_run.meta_json,
            "llm_error": str(exc),
        }

    item.research_data = {
        "generation_payload": generation_payload,
        "generated_at": datetime.now(UTC).isoformat(),
        "generation_mode": result_mode,
    }
    item.article_review = {
        "status": "pending_human_review",
        "summary": generation_payload.get("summary", "Draft prepared."),
        "hook": generation_payload.get("hook"),
        "cta": generation_payload.get("cta"),
        "review_notes": generation_payload.get("review_notes", []),
        "last_manual_job_id": str(job_run.id),
        "generation_mode": result_mode,
    }
    item.status = "draft"

    job_run.status = "completed"
    job_run.finished_at = datetime.now(UTC)
    job_run.meta_json = {
        **job_run.meta_json,
        "result": result_mode,
        "item_status_after_run": item.status,
        "draft_title": generation_payload.get("draft_title"),
    }

    await session.commit()
    await session.refresh(job_run)

    return StartGenerationResponse(
        job_run=job_run,
        item_status=item.status,
    )
