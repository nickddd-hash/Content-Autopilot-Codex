from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import settings
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BrandProfile, ContentPlan, ContentPlanItem, JobRun, Product
from app.models.evaluator import ContentEvaluationResult
from app.schemas.job_run import StartGenerationResponse
from app.services.generation_prompt import build_generation_messages
from app.services.content_evaluation import evaluate_item_content
from app.services.llm_client import LLMClientError, generate_json
from app.services.research_sonar import run_sonar_followup, run_sonar_research
from app.services.text_normalization import normalize_user_facing_text, strip_markdown

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
    plan_statement = select(ContentPlan).where(ContentPlan.id == plan_id).options(selectinload(ContentPlan.product))
    plan = await session.scalar(plan_statement)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found.")

    item_statement = (
        select(ContentPlanItem)
        .where(
            ContentPlanItem.id == item_id,
            ContentPlanItem.plan_id == plan_id,
        )
        .options(selectinload(ContentPlanItem.evaluation_results).selectinload(ContentEvaluationResult.evaluator))
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


def _should_enforce_telegram_caption_limit(item: ContentPlanItem) -> bool:
    if not isinstance(item.research_data, dict):
        return False

    # If Userbot is configured, we allow longreads and don't enforce the strict caption limit.
    if settings.telegram_api_id and settings.telegram_api_hash:
        return False

    raw_channels = item.research_data.get("channel_targets")
    channels = [str(channel).strip().lower() for channel in raw_channels] if isinstance(raw_channels, list) else []
    include_illustration = item.research_data.get("include_illustration")

    return "telegram" in channels and include_illustration is True


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

    return normalized[: max(0, limit - 1)].rstrip() + "…"


def _enforce_publishable_telegram_payload(item: ContentPlanItem, generation_payload: dict[str, Any]) -> dict[str, Any]:
    # We disable automatic shortening to allow for maximum depth and holistic facts.
    # Readability and impact will be assessed by AI evaluators instead of hard limits.
    return generation_payload


def _build_fallback_generation_payload(item: ContentPlanItem, product: Product | None) -> dict[str, Any]:
    product_name = product.name if product else "Product"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_mode": "failed_stub",
        "draft_title": item.title,
        "draft_markdown": (
            "🔴 ОШИБКА ГЕНЕРАЦИИ\n\n"
            "Не удалось сгенерировать контент из-за временного ограничения API (лимиты запросов).\n"
            "Пожалуйста, нажмите «Перегенерировать» через 1-2 минуты.\n\n"
            f"Тема: {item.title}\n"
            f"Тезис: {item.angle or 'Не указан'}"
        ),
        "summary": "Генерация не удалась (ошибка лимитов).",
        "hook": "Ошибка генерации.",
        "cta": "Попробовать позже.",
        "repurposing": {
            "post": "Ошибка",
            "carousel": [],
            "reel_script": "Ошибка",
        },
        "review_notes": [
            "ВНИМАНИЕ: Это не готовый пост, а заглушка ошибки.",
            "Нажмите кнопку перегенерации, когда лимиты API восстановятся.",
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
        "generated_draft_markdown": normalize_user_facing_text(strip_markdown(str(generation_payload.get("draft_markdown")))) if generation_payload.get("draft_markdown") else None,
        "generated_summary": normalize_user_facing_text(str(generation_payload.get("summary"))) if generation_payload.get("summary") else None,
        "generated_hook": normalize_user_facing_text(str(generation_payload.get("hook"))) if generation_payload.get("hook") else None,
        "generated_cta": normalize_user_facing_text(str(generation_payload.get("cta"))) if generation_payload.get("cta") else None,
        "generated_asset_brief": normalize_user_facing_text(str(generation_payload.get("asset_brief"))) if generation_payload.get("asset_brief") else None,
        "generation_mode": item.article_review.get("generation_mode") if isinstance(item.article_review, dict) else None,
        "evaluation_results": item.evaluation_results,
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

    content_direction = ""
    if isinstance(item.research_data, dict):
        raw_direction = item.research_data.get("content_direction")
        if isinstance(raw_direction, str):
            content_direction = raw_direction.strip().lower()

    research_context = await run_sonar_research(
        topic=item.title,
        angle=item.angle,
        direction=content_direction,
        session=session,
    )

    try:
        messages = build_generation_messages(plan.product, brand_profile, plan, item, research_context=research_context)
        generation_payload = await generate_json(messages, session=session)

        followup_query = generation_payload.get("research_followup")
        if isinstance(followup_query, str) and followup_query.strip():
            additional = await run_sonar_followup(followup_query.strip(), session=session)
            if additional:
                combined_context = f"{research_context}\n\n---\n\nДополнительные данные:\n{additional}"
                messages = build_generation_messages(plan.product, brand_profile, plan, item, research_context=combined_context)
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

    # Start evaluation in background
    import asyncio
    async def _bg_eval():
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as bg_session:
            try:
                await evaluate_item_content(bg_session, item.id)
            except Exception:
                pass
    
    asyncio.create_task(_bg_eval())

    return StartGenerationResponse(
        job_run=job_run,
        item_status=item.status,
    )


async def regenerate_item_visual_brief(
    session: AsyncSession,
    plan_id: UUID,
    item_id: UUID,
) -> dict[str, Any]:
    plan, item = await get_content_plan_item_or_404(session, plan_id, item_id)
    
    # We need the full context of the post to generate a good brief
    research_data = item.research_data if isinstance(item.research_data, dict) else {}
    generation_payload = research_data.get("generation_payload", {})
    if not isinstance(generation_payload, dict):
        generation_payload = {}
        
    content_text = generation_payload.get("draft_markdown", "")
    if not content_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate visual brief without post content.")

    system_prompt = (
        "You are a visual creative director. Your job is to create a detailed visual brief for an editorial illustration.\n"
        "The illustration will accompany a specific blog post.\n"
        "Guidelines:\n"
        "- MANDATORY: Include a human factor or something alive (person, expert, hands, student, silhouette).\n"
        "- Style: clean, modern, trustworthy, editorial.\n"
        "- Metaphor: use a clever visual metaphor related to the post content.\n"
        "- Details: specify lighting, mood, and square composition.\n"
        "- NO TEXT in the image.\n"
        "Return valid JSON: {\"asset_brief\": \"string\"}"
    )
    user_prompt = f"Post content:\n\n{content_text}"

    payload = await generate_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        session=session,
    )

    new_brief = payload.get("asset_brief", "")
    if not new_brief:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to generate visual brief.")

    # Update item
    generation_payload["asset_brief"] = new_brief
    research_data["generation_payload"] = generation_payload
    item.research_data = research_data
    
    # Reset evaluations because the visual concept changed
    await session.execute(
        delete(ContentEvaluationResult)
        .where(ContentEvaluationResult.content_plan_item_id == item.id)
    )
    
    await session.commit()
    
    # Trigger new evaluation in background
    import asyncio
    async def _bg_eval():
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as bg_session:
            try:
                await evaluate_item_content(bg_session, item.id)
            except Exception:
                pass
    
    asyncio.create_task(_bg_eval())

    await session.refresh(item)
    return item
