from __future__ import annotations

from datetime import datetime, timezone
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


def _get_active_channel_platforms(product: Product | None) -> list[str]:
    if product is None:
        return []

    platforms: list[str] = []
    for channel in getattr(product, "channels", []) or []:
        if not getattr(channel, "is_active", True):
            continue
        platform = (getattr(channel, "platform", "") or "").strip().lower()
        if platform and platform not in platforms:
            platforms.append(platform)

    for channel in (getattr(product, "primary_channels", []) or []):
        platform = (channel or "").strip().lower()
        if platform and platform not in platforms:
            platforms.append(platform)

    return platforms


async def get_content_plan_item_or_404(
    session: AsyncSession,
    plan_id: UUID,
    item_id: UUID,
) -> tuple[ContentPlan, ContentPlanItem]:
    plan_statement = (
        select(ContentPlan)
        .where(ContentPlan.id == plan_id)
        .options(selectinload(ContentPlan.product).selectinload(Product.channels))
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


def _build_channel_adaptations(item: ContentPlanItem, platforms: list[str]) -> dict[str, dict[str, str]]:
    adaptations: dict[str, dict[str, str]] = {}
    for platform in platforms:
        if platform == "telegram":
            adaptations[platform] = {
                "format": "telegram_post",
                "content_markdown": f"{item.title}\n\nКороткий Telegram-пост с сильным хуком и практической пользой.",
                "asset_brief": "",
            }
        elif platform == "instagram":
            adaptations[platform] = {
                "format": "carousel_or_reel",
                "content_markdown": f"{item.title}\n\nInstagram-адаптация с короткими смысловыми блоками и визуальной опорой.",
                "asset_brief": "Carousel with 5-7 slides or a short reel with one concrete example.",
            }
        elif platform == "youtube":
            adaptations[platform] = {
                "format": "video_script",
                "content_markdown": f"{item.title}\n\nShort video angle with one problem, one example, and one takeaway.",
                "asset_brief": "Talking-head or demo-style short video.",
            }
        elif platform == "blog":
            adaptations[platform] = {
                "format": "long_form_article",
                "content_markdown": f"{item.title}\n\nStructured long-form version with a clear intro, examples, and takeaway.",
                "asset_brief": "One simple illustration or screenshot-based explainer.",
            }
        else:
            adaptations[platform] = {
                "format": "adapted_post",
                "content_markdown": f"{item.title}\n\nAdapted version for {platform}.",
                "asset_brief": "",
            }

    return adaptations


def _build_fallback_generation_payload(item: ContentPlanItem, product: Product | None) -> dict[str, Any]:
    product_name = product.name if product else "Product"
    channel_targets = _get_active_channel_platforms(product)
    channel_adaptations = _build_channel_adaptations(item, channel_targets)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_mode": "fallback_stub",
        "draft_title": item.title,
        "draft_markdown": (
            f"# {item.title}\n\n"
            f"{item.angle or 'This topic helps the reader understand the problem and see a realistic next step.'}\n\n"
            "Core idea:\n"
            "- explain the real problem simply;\n"
            "- show one practical takeaway;\n"
            "- keep the structure reusable across multiple channels.\n"
        ),
        "summary": f"Fallback draft for {product_name}.",
        "hook": "Why do people keep hearing about a useful idea, but still do nothing with it?",
        "cta": "If you want a concrete next step instead of generic advice, this topic should lead into a simple practical action.",
        "channel_adaptations": channel_adaptations,
        "repurposing": {
            "post": f"Short post version for: {item.title}",
            "carousel": [
                "Slide 1: the actual problem",
                "Slide 2: what changes in practice",
                "Slide 3: one clear next step",
            ],
            "reel_script": f"Short reel script for: {item.title}",
        },
        "review_notes": [
            "LLM generation failed, so this is a fallback content package.",
            "A human should check tone and channel fit before publishing.",
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
        "channel_adaptations": generation_payload.get("channel_adaptations", {}),
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
    now = datetime.now(timezone.utc)
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
        generation_payload = await generate_json(messages, session=session)
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
    job_run.finished_at = datetime.now(timezone.utc)
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
