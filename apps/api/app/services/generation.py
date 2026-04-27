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
from app.services.channel_profiles import resolve_dzen_format_mode, resolve_dzen_output_format
from app.services.generation_prompt import build_generation_messages
from app.services.llm_client import LLMClientError, generate_json
from app.services.text_normalization import normalize_user_facing_text

TELEGRAM_CAPTION_SAFE_LIMIT = 900

ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"draft", "archived"},
    "draft": {"review-ready", "planned", "archived"},
    "review-ready": {"draft", "published", "failed", "archived"},
    "failed": {"planned", "draft", "archived"},
    "published": {"archived"},
    "archived": {"draft", "planned"},
}


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


def _sanitize_text(value: str) -> str:
    return normalize_user_facing_text(value)


def _sanitize_generation_payload(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [_sanitize_generation_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_generation_payload(item) for key, item in value.items()}
    return value


def _normalize_channel_list(raw_channels: Any) -> list[str]:
    if not isinstance(raw_channels, list):
        return []

    normalized: list[str] = []
    for channel in raw_channels:
        value = str(channel).strip().lower()
        if value:
            normalized.append(value)
    return normalized


def _get_selected_channels(item: ContentPlanItem, product: Product | None = None) -> list[str]:
    if isinstance(item.research_data, dict):
        selected_channels = _normalize_channel_list(item.research_data.get("channel_targets"))
        if selected_channels:
            return selected_channels

    if product is not None:
        product_channels = _normalize_channel_list(product.primary_channels)
        if product_channels:
            return product_channels

    return ["telegram"]


def _build_channel_adaptations(item: ContentPlanItem, generation_payload: dict[str, Any], channels: list[str]) -> dict[str, dict[str, str]]:
    raw_adaptations = generation_payload.get("channel_adaptations")
    normalized_adaptations: dict[str, dict[str, str]] = {}
    if isinstance(raw_adaptations, dict):
        for channel_key, adaptation in raw_adaptations.items():
            normalized_channel = str(channel_key).strip().lower()
            if not normalized_channel or not isinstance(adaptation, dict):
                continue
            normalized_adaptations[normalized_channel] = {
                key: str(value).strip()
                for key, value in adaptation.items()
                if isinstance(value, str) and str(value).strip()
            }

    research_data = item.research_data if isinstance(item.research_data, dict) else {}
    draft_title = str(generation_payload.get("draft_title") or item.title or "").strip()
    draft_markdown = str(generation_payload.get("draft_markdown") or "").strip()
    summary = str(generation_payload.get("summary") or item.angle or "").strip()
    asset_brief = str(research_data.get("asset_brief") or generation_payload.get("asset_brief") or "").strip()
    dzen_output_format = resolve_dzen_output_format(
        research_data.get("content_direction"),
        resolve_dzen_format_mode(None, research_data),
    )

    if "telegram" in channels:
        telegram_adaptation = normalized_adaptations.get("telegram", {})
        telegram_adaptation.setdefault("format", "telegram_post")
        if draft_markdown and not telegram_adaptation.get("content_markdown"):
            telegram_adaptation["content_markdown"] = draft_markdown
        if asset_brief and not telegram_adaptation.get("asset_brief"):
            telegram_adaptation["asset_brief"] = asset_brief
        normalized_adaptations["telegram"] = telegram_adaptation

    if "dzen" in channels:
        dzen_adaptation = normalized_adaptations.get("dzen", {})
        dzen_adaptation.setdefault("format", dzen_output_format)
        if not dzen_adaptation.get("content_markdown"):
            lead = summary or draft_markdown
            title_line = draft_title
            if dzen_output_format == "dzen_post":
                dzen_adaptation["content_markdown"] = "\n\n".join(
                    part
                    for part in [
                        title_line,
                        draft_markdown or lead,
                    ]
                    if part
                ).strip()
            else:
                dzen_adaptation["content_markdown"] = "\n\n".join(
                    part
                    for part in [
                        title_line,
                        lead,
                        draft_markdown if draft_markdown and draft_markdown != lead else "",
                    ]
                    if part
                ).strip()
        if asset_brief and not dzen_adaptation.get("asset_brief"):
            dzen_adaptation["asset_brief"] = asset_brief
        normalized_adaptations["dzen"] = dzen_adaptation

    return normalized_adaptations


def _should_enforce_telegram_caption_limit(item: ContentPlanItem) -> bool:
    if not isinstance(item.research_data, dict):
        return True

    channels = _normalize_channel_list(item.research_data.get("channel_targets"))
    include_illustration = item.research_data.get("include_illustration", True)

    # Planned items default to Telegram posts with illustrations. Custom posts
    # can opt out by setting include_illustration=False.
    return (not channels or "telegram" in channels) and include_illustration is not False


def _shorten_text_to_limit(text: str, limit: int) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized

    paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]
    if paragraphs:
        collected: list[str] = []
        for paragraph in paragraphs:
            candidate = "\n\n".join([*collected, paragraph]).strip()
            if len(candidate) <= limit:
                collected.append(paragraph)
                continue
            break
        if collected:
            return "\n\n".join(collected).strip()

    sentences = [sentence.strip() for sentence in normalized.replace("\n", " ").split(". ") if sentence.strip()]
    if sentences:
        collected_sentences: list[str] = []
        for sentence in sentences:
            candidate = ". ".join([*collected_sentences, sentence]).strip()
            if len(candidate) + 1 <= limit:
                collected_sentences.append(sentence.rstrip("."))
                continue
            break
        if collected_sentences:
            return ". ".join(collected_sentences).strip().rstrip(".") + "."

    return normalized[: max(0, limit - 3)].rstrip() + "..."


def _enforce_publishable_telegram_payload(item: ContentPlanItem, generation_payload: dict[str, Any]) -> dict[str, Any]:
    if not _should_enforce_telegram_caption_limit(item):
        return generation_payload

    payload = dict(generation_payload)
    draft_markdown = str(payload.get("draft_markdown") or "").strip()
    if not draft_markdown:
        return payload

    shortened_markdown = _shorten_text_to_limit(draft_markdown, TELEGRAM_CAPTION_SAFE_LIMIT)
    if shortened_markdown == draft_markdown:
        return payload

    payload["draft_markdown"] = shortened_markdown

    review_notes = payload.get("review_notes")
    normalized_notes = [str(note) for note in review_notes if note] if isinstance(review_notes, list) else []
    normalized_notes.append("Текст автоматически ужат под один Telegram-пост с иллюстрацией.")
    payload["review_notes"] = normalized_notes
    return payload


def _build_fallback_generation_payload(item: ContentPlanItem, product: Product | None) -> dict[str, Any]:
    product_name = product.name if product else "Product"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_mode": "fallback_stub",
        "draft_title": item.title,
        "draft_markdown": (
            f"{item.title}\n\n"
            f"{item.angle or 'Эта тема помогает быстро понять проблему и увидеть следующий рабочий шаг.'}\n\n"
            "Обычно хаос начинается не с отсутствия инструментов, а с отсутствия понятного сценария. "
            "Если показать один конкретный процесс, где AI реально экономит время, вход в тему становится спокойнее.\n\n"
            "Начать лучше с одной повторяющейся задачи и посмотреть, что можно упростить уже на этой неделе."
        ),
        "summary": f"Черновой fallback draft для {product_name}.",
        "hook": "Если AI до сих пор кажется сложной игрушкой, проблема часто не в AI, а в подаче.",
        "cta": "Если хотите, можно разобрать один ваш процесс и понять, где автоматизация даст реальную пользу.",
        "repurposing": {
            "post": f"Короткий пост по теме: {item.title}",
            "carousel": [
                "Где болит сильнее всего",
                "Какой рабочий сценарий помогает первым",
            ],
            "reel_script": f"Короткий видео-сценарий по теме: {item.title}",
        },
        "review_notes": [
            "Черновик сохранён в fallback-режиме и может требовать ручной докрутки.",
            "После восстановления основной модели стоит перегенерировать текст.",
        ],
    }
    payload["channel_adaptations"] = _build_channel_adaptations(item, payload, _get_selected_channels(item, product))
    return payload


def build_content_plan_item_detail(item: ContentPlanItem) -> dict[str, Any]:
    generation_payload = {}
    if isinstance(item.research_data, dict):
        generation_payload = item.research_data.get("generation_payload", {})

    if not isinstance(generation_payload, dict):
        generation_payload = {}

    channel_adaptations = _build_channel_adaptations(item, generation_payload, _get_selected_channels(item))

    return {
        "id": item.id,
        "plan_id": item.plan_id,
        "order": item.order,
        "title": normalize_user_facing_text(item.title),
        "angle": normalize_user_facing_text(item.angle) if isinstance(item.angle, str) else item.angle,
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
        "generated_draft_title": normalize_user_facing_text(str(generation_payload.get("draft_title"))) if generation_payload.get("draft_title") else None,
        "generated_draft_markdown": normalize_user_facing_text(str(generation_payload.get("draft_markdown"))) if generation_payload.get("draft_markdown") else None,
        "generated_summary": normalize_user_facing_text(str(generation_payload.get("summary"))) if generation_payload.get("summary") else None,
        "generated_hook": normalize_user_facing_text(str(generation_payload.get("hook"))) if generation_payload.get("hook") else None,
        "generated_cta": normalize_user_facing_text(str(generation_payload.get("cta"))) if generation_payload.get("cta") else None,
        "channel_adaptations": channel_adaptations,
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

    generation_payload = _sanitize_generation_payload(generation_payload)
    if isinstance(generation_payload, dict):
        generation_payload = _enforce_publishable_telegram_payload(item, generation_payload)
        generation_payload["channel_adaptations"] = _build_channel_adaptations(
            item,
            generation_payload,
            _get_selected_channels(item, plan.product),
        )
    existing_research_data = item.research_data if isinstance(item.research_data, dict) else {}

    item.research_data = {
        **existing_research_data,
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
