from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import ContentPlan, ContentPlanItem, ProductChannel
from app.services.text_normalization import normalize_user_facing_text

TELEGRAM_CAPTION_LIMIT = 1024


def _extract_generated_image(item: ContentPlanItem) -> dict[str, Any] | None:
    if not isinstance(item.research_data, dict):
        return None
    generated_image = item.research_data.get("generated_image")
    if not isinstance(generated_image, dict):
        return None
    return generated_image


def _extract_draft(item: ContentPlanItem) -> tuple[str, str]:
    if not isinstance(item.research_data, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="У поста ещё нет сгенерированного текста.")

    generation_payload = item.research_data.get("generation_payload")
    if not isinstance(generation_payload, dict):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="У поста ещё нет сгенерированного текста.")

    title = normalize_user_facing_text(str(generation_payload.get("draft_title") or item.title or ""))
    markdown = normalize_user_facing_text(str(generation_payload.get("draft_markdown") or ""))
    if not markdown:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="У поста ещё нет сгенерированного текста.")
    return title, markdown


def _resolve_generated_image_path(item: ContentPlanItem) -> tuple[Path, str] | None:
    generated_image = _extract_generated_image(item)
    if not generated_image:
        return None

    image_url = str(generated_image.get("url") or "").strip()
    mime_type = str(generated_image.get("mime_type") or "image/png").strip() or "image/png"
    if not image_url:
        return None

    file_name = Path(image_url).name
    file_path = Path(settings.media_storage_dir) / file_name
    if not file_path.exists():
        return None
    return file_path, mime_type


def _build_single_telegram_post_text(title: str, draft_markdown: str) -> str:
    draft = draft_markdown.strip()
    headline = title.strip()

    if headline:
        lowered_draft = draft.lower()
        lowered_headline = headline.lower()
        if not lowered_draft.startswith(lowered_headline):
            combined = f"{headline}\n\n{draft}"
            if len(combined) <= TELEGRAM_CAPTION_LIMIT:
                return combined

    return draft


def _format_telegram_post_html(title: str, draft_markdown: str) -> str:
    draft = draft_markdown.strip()
    headline = title.strip()

    if not headline:
        return escape(draft)

    lowered_draft = draft.lower()
    lowered_headline = headline.lower()
    if lowered_draft.startswith(lowered_headline):
        body = draft[len(headline) :].lstrip()
        if body:
            return f"<b>{escape(headline)}</b>\n\n{escape(body)}"
        return f"<b>{escape(headline)}</b>"

    return f"<b>{escape(headline)}</b>\n\n{escape(draft)}"


async def _telegram_api_request(
    bot_token: str,
    method: str,
    *,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/{method}",
                data=data,
                files=files,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось отправить пост в Telegram: {exc}",
        ) from exc

    payload = response.json()
    if not payload.get("ok"):
        description = str(payload.get("description") or "Telegram не принял публикацию.")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=description)
    return payload.get("result") or {}


async def publish_item_to_telegram_channels(
    session: AsyncSession,
    plan: ContentPlan,
    item: ContentPlanItem,
    telegram_channels: list[ProductChannel],
) -> ContentPlanItem:
    if not telegram_channels:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У проекта нет подключённого и проверенного Telegram-канала для публикации.",
        )

    title, draft_markdown = _extract_draft(item)
    image_info = _resolve_generated_image_path(item)
    publication_records: list[dict[str, Any]] = []

    for channel in telegram_channels:
        bot_token = str(channel.secrets_json.get("bot_token") or "").strip()
        chat_id = str(channel.settings_json.get("chat_id") or "").strip()
        if not bot_token or not chat_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"В канале {channel.name} не хватает bot_token или chat_id.",
            )

        message_ids: list[int] = []
        single_post_text = _build_single_telegram_post_text(title, draft_markdown)
        if image_info:
            if len(single_post_text) > TELEGRAM_CAPTION_LIMIT:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Для публикации одним Telegram-постом с иллюстрацией текст должен помещаться в подпись "
                        f"до {TELEGRAM_CAPTION_LIMIT} символов. Сократите текст и сохраните правки."
                    ),
                )

            file_path, mime_type = image_info
            photo_result = await _telegram_api_request(
                bot_token,
                "sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": _format_telegram_post_html(title, draft_markdown),
                    "parse_mode": "HTML",
                },
                files={
                    "photo": (
                        file_path.name,
                        file_path.read_bytes(),
                        mime_type,
                    )
                },
            )
            if isinstance(photo_result.get("message_id"), int):
                message_ids.append(photo_result["message_id"])
        else:
            text_result = await _telegram_api_request(
                bot_token,
                "sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": _format_telegram_post_html(title, draft_markdown),
                    "parse_mode": "HTML",
                    "disable_web_page_preview": "true",
                },
            )
            if isinstance(text_result.get("message_id"), int):
                message_ids.append(text_result["message_id"])

        publication_records.append(
            {
                "platform": "telegram",
                "channel_id": str(channel.id),
                "channel_name": channel.name,
                "chat_id": chat_id,
                "message_ids": message_ids,
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    research_data = dict(item.research_data) if isinstance(item.research_data, dict) else {}
    existing_publications = research_data.get("publications")
    publications = dict(existing_publications) if isinstance(existing_publications, dict) else {}
    publications["telegram"] = publication_records
    research_data["publications"] = publications
    item.research_data = research_data
    item.status = "published"
    item.published_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(item)
    return item
