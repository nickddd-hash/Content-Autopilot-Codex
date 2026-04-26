from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import ContentPlan, ContentPlanItem, JobRun, Product, ProductChannel
from app.services.generation import build_content_plan_item_detail, start_manual_generation
from app.services.media_generator import generate_illustration_for_item
from app.services.plan_generation import generate_plan_items_for_plan
from app.services.telegram_publisher import publish_item_to_telegram_channels

logger = logging.getLogger(__name__)
_ACTIVE_PLAN_PIPELINE_TASKS: dict[UUID, asyncio.Task] = {}


def _log_background_task_result(job_id: UUID, task: asyncio.Task) -> None:
    _ACTIVE_PLAN_PIPELINE_TASKS.pop(job_id, None)
    try:
        task.result()
    except asyncio.CancelledError:
        return
    except Exception:
        logger.exception("Plan pipeline background task crashed.")


def _normalize_publish_days(raw_days: list[int] | None) -> set[int]:
    days = [int(day) for day in (raw_days or [])]
    if not days:
        return {1, 4}
    if all(1 <= day <= 7 for day in days):
        return set(days)
    return {((day % 7) + 1) for day in days}


def _parse_publish_time(value: str | None) -> time:
    raw_value = (value or "07:00").strip()
    try:
        hours, minutes = raw_value.split(":", 1)
        return time(hour=int(hours), minute=int(minutes), tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return time(hour=7, minute=0, tzinfo=timezone.utc)


def _build_schedule_slots(
    *,
    count: int,
    publish_days: list[int] | None,
    publish_time_utc: str | None,
    start_at: datetime,
) -> list[datetime]:
    weekday_set = _normalize_publish_days(publish_days)
    publish_clock = _parse_publish_time(publish_time_utc)
    slots: list[datetime] = []
    cursor = start_at.astimezone(timezone.utc).replace(second=0, microsecond=0)

    for offset in range(0, 120):
        candidate_date = (cursor + timedelta(days=offset)).date()
        if candidate_date.isoweekday() not in weekday_set:
            continue

        candidate = datetime.combine(candidate_date, publish_clock, tzinfo=timezone.utc)
        if candidate <= cursor:
            continue

        slots.append(candidate)
        if len(slots) >= count:
            break

    if len(slots) < count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Не удалось разметить календарь публикаций для всего плана.",
        )
    return slots


async def _get_plan_with_product(session: AsyncSession, plan_id: UUID) -> ContentPlan:
    statement = (
        select(ContentPlan)
        .where(ContentPlan.id == plan_id)
        .options(selectinload(ContentPlan.items))
        .options(selectinload(ContentPlan.product).selectinload(Product.content_settings))
        .options(selectinload(ContentPlan.product).selectinload(Product.channels))
    )
    plan = await session.scalar(statement)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found.")
    return plan


async def get_latest_item_job(session: AsyncSession, item_id: UUID) -> JobRun | None:
    statement = (
        select(JobRun)
        .where(JobRun.content_plan_item_id == item_id)
        .order_by(JobRun.created_at.desc())
        .limit(1)
    )
    return await session.scalar(statement)


async def get_latest_plan_job(session: AsyncSession, plan_id: UUID) -> JobRun | None:
    statement = (
        select(JobRun)
        .where(JobRun.content_plan_id == plan_id)
        .order_by(JobRun.created_at.desc())
        .limit(1)
    )
    return await session.scalar(statement)


async def build_plan_materials(session: AsyncSession, plan_id: UUID) -> list[dict]:
    plan = await _get_plan_with_product(session, plan_id)
    ordered_items = sorted(plan.items, key=lambda item: item.order)
    plan_settings = dict(plan.settings_json or {})
    auto_generate_illustrations = plan_settings.get("auto_generate_illustrations", True) is True

    for item in ordered_items:
        if item.status == "archived":
            continue

        generation_payload = item.research_data.get("generation_payload", {}) if isinstance(item.research_data, dict) else {}
        has_draft = isinstance(generation_payload, dict) and bool(str(generation_payload.get("draft_markdown") or "").strip())
        has_image = isinstance(item.research_data, dict) and isinstance(item.research_data.get("generated_image"), dict)

        if not has_draft:
            await start_manual_generation(session, plan.id, item.id, notes="Triggered from build materials flow")
            item = await session.get(ContentPlanItem, item.id)
            if item is None:
                continue

        if auto_generate_illustrations and not has_image:
            await generate_illustration_for_item(session, item)

        if item.status == "planned":
            item.status = "draft"

    content_settings = plan.product.content_settings
    autopost_enabled = bool(content_settings and content_settings.autopilot_enabled and content_settings.social_posting_enabled)
    schedulable_items = [item for item in ordered_items if item.published_at is None and item.status != "archived"]
    if schedulable_items and content_settings is not None:
        schedule_slots = _build_schedule_slots(
            count=len(schedulable_items),
            publish_days=content_settings.publish_days,
            publish_time_utc=content_settings.publish_time_utc,
            start_at=datetime.now(timezone.utc),
        )
        for item, slot in zip(schedulable_items, schedule_slots, strict=False):
            item.scheduled_at = slot
            if autopost_enabled and item.status == "draft":
                item.status = "review-ready"

    plan_settings["needs_reschedule"] = False
    plan_settings["reschedule_reason"] = None
    plan_settings["reschedule_source_item_id"] = None
    plan.settings_json = plan_settings

    await session.commit()
    refreshed_plan = await _get_plan_with_product(session, plan_id)
    return [build_content_plan_item_detail(item) for item in sorted(refreshed_plan.items, key=lambda current: current.order)]


async def _run_plan_pipeline_job(
    *,
    job_id: UUID,
    plan_id: UUID,
    generate_items: bool,
    theme_override: str | None,
    num_items_override: int | None,
) -> None:
    async with AsyncSessionLocal() as session:
        job = await session.get(JobRun, job_id)
        if job is None:
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

    try:
        async with AsyncSessionLocal() as session:
            if generate_items:
                await generate_plan_items_for_plan(
                    session,
                    plan_id,
                    theme_override=theme_override,
                    num_items_override=num_items_override,
                )
            built_items = await build_plan_materials(session, plan_id)

        async with AsyncSessionLocal() as session:
            job = await session.get(JobRun, job_id)
            if job is None:
                return

            job.status = "completed"
            job.finished_at = datetime.now(timezone.utc)
            job.error_message = None
            job.meta_json = {
                **(job.meta_json or {}),
                "built_items_count": len(built_items),
                "result": "completed",
            }
            await session.commit()
    except asyncio.CancelledError:
        async with AsyncSessionLocal() as session:
            job = await session.get(JobRun, job_id)
            if job is not None and job.status in ("pending", "running"):
                job.status = "cancelled"
                job.finished_at = datetime.now(timezone.utc)
                job.error_message = "Stopped manually by operator request"
                job.meta_json = {
                    **(job.meta_json or {}),
                    "result": "cancelled",
                }
                await session.commit()
    except Exception as exc:
        logger.exception("Plan pipeline job failed: job_id=%s plan_id=%s", job_id, plan_id)
        async with AsyncSessionLocal() as session:
            job = await session.get(JobRun, job_id)
            if job is None:
                return

            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            job.error_message = str(exc)
            job.meta_json = {
                **(job.meta_json or {}),
                "result": "failed",
            }
            await session.commit()


async def start_plan_pipeline_job(
    session: AsyncSession,
    plan_id: UUID,
    *,
    generate_items: bool = False,
    theme_override: str | None = None,
    num_items_override: int | None = None,
) -> JobRun:
    plan = await _get_plan_with_product(session, plan_id)
    active_statement = (
        select(JobRun)
        .where(JobRun.content_plan_id == plan.id)
        .where(JobRun.status.in_(("pending", "running")))
        .limit(1)
    )
    active_job = await session.scalar(active_statement)
    if active_job is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plan generation is already running.",
        )

    now = datetime.now(timezone.utc)
    job_type = "plan_generation_pipeline" if generate_items else "plan_material_build"
    job = JobRun(
        job_type=job_type,
        status="pending",
        product_id=plan.product_id,
        content_plan_id=plan.id,
        started_at=now,
        meta_json={
            "plan_id": str(plan.id),
            "generate_items": generate_items,
            "theme_override": theme_override,
            "num_items_override": num_items_override,
        },
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    task = asyncio.create_task(
        _run_plan_pipeline_job(
            job_id=job.id,
            plan_id=plan.id,
            generate_items=generate_items,
            theme_override=theme_override,
            num_items_override=num_items_override,
        )
    )
    _ACTIVE_PLAN_PIPELINE_TASKS[job.id] = task
    task.add_done_callback(lambda finished_task: _log_background_task_result(job.id, finished_task))
    return job


async def cancel_plan_pipeline_job(session: AsyncSession, plan_id: UUID) -> JobRun:
    await _get_plan_with_product(session, plan_id)
    statement = (
        select(JobRun)
        .where(JobRun.content_plan_id == plan_id)
        .where(JobRun.status.in_(("pending", "running")))
        .order_by(JobRun.created_at.desc())
        .limit(1)
    )
    job = await session.scalar(statement)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active plan generation job not found.")

    task = _ACTIVE_PLAN_PIPELINE_TASKS.get(job.id)
    if task is not None and not task.done():
        task.cancel()

    job.status = "cancelled"
    job.finished_at = datetime.now(timezone.utc)
    job.error_message = "Stopped manually by operator request"
    job.meta_json = {
        **(job.meta_json or {}),
        "result": "cancelled",
    }
    await session.commit()
    await session.refresh(job)
    return job


async def publish_plan_item_now(session: AsyncSession, plan_id: UUID, item_id: UUID) -> dict:
    plan = await _get_plan_with_product(session, plan_id)
    item = next((current for current in plan.items if current.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan item not found.")

    telegram_channels = [
        channel
        for channel in plan.product.channels
        if channel.platform == "telegram" and channel.validation_status == "valid" and channel.is_active
    ]
    selected_channels = []
    if isinstance(item.research_data, dict):
        raw_targets = item.research_data.get("channel_targets")
        if isinstance(raw_targets, list):
            selected_channels = [str(target).strip().lower() for target in raw_targets if str(target).strip()]
    if selected_channels:
        telegram_channels = [channel for channel in telegram_channels if channel.platform in selected_channels]

    now = datetime.now(timezone.utc)
    if item.scheduled_at and item.scheduled_at > now:
        plan_settings = dict(plan.settings_json or {})
        plan_settings["needs_reschedule"] = True
        plan_settings["reschedule_reason"] = "published_early"
        plan_settings["reschedule_source_item_id"] = str(item.id)
        plan.settings_json = plan_settings

    item = await publish_item_to_telegram_channels(session, plan, item, telegram_channels)
    return build_content_plan_item_detail(item)


async def process_due_autopost_items(session: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    statement = (
        select(ContentPlanItem)
        .where(ContentPlanItem.status.in_(("review-ready", "draft")))
        .where(ContentPlanItem.published_at.is_(None))
        .where(ContentPlanItem.scheduled_at.is_not(None))
        .where(ContentPlanItem.scheduled_at <= now)
        .options(selectinload(ContentPlanItem.plan).selectinload(ContentPlan.product).selectinload(Product.content_settings))
        .options(selectinload(ContentPlanItem.plan).selectinload(ContentPlan.product).selectinload(Product.channels))
        .order_by(ContentPlanItem.scheduled_at.asc())
    )
    result = await session.execute(statement)
    items = list(result.scalars().unique().all())
    published_count = 0

    for item in items:
        plan = item.plan
        if plan is None or plan.product is None or plan.product.content_settings is None:
            continue

        settings = plan.product.content_settings
        if not settings.autopilot_enabled or not settings.social_posting_enabled:
            continue

        telegram_channels = [
            channel
            for channel in plan.product.channels
            if channel.platform == "telegram" and channel.validation_status == "valid" and channel.is_active
        ]
        if not telegram_channels:
            continue

        try:
            await publish_item_to_telegram_channels(session, plan, item, telegram_channels)
            published_count += 1
        except HTTPException as exc:
            item.retry_count += 1
            item.error_message = str(exc.detail or "Автопостинг не смог отправить материал в Telegram.")
            logger.warning("Autopost failed for item %s: %s", item.id, item.error_message)
            await session.commit()
        except Exception as exc:
            item.retry_count += 1
            item.error_message = f"Автопостинг не смог отправить материал в Telegram: {exc}"
            logger.exception("Unexpected autopost failure for item %s.", item.id)
            await session.commit()

    return published_count
