from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from pathlib import Path
import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content_plan import ContentPlanItem
from app.models.system import SystemSetting


MEDIA_OUTPUT_DIR = Path(settings.media_storage_dir)
OPENAI_IMAGE_BASE_URL = "https://api.openai.com/v1"
OPENAI_IMAGE_MODEL = "gpt-image-1"
OPENROUTER_IMAGE_BASE_URL = "https://openrouter.ai/api/v1"
ALLOWED_UPLOAD_MIME_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


def _purge_item_media_files(item: ContentPlanItem, pattern: str) -> None:
    for existing_file in MEDIA_OUTPUT_DIR.glob(pattern):
        existing_file.unlink(missing_ok=True)


async def _read_system_setting(session: AsyncSession, key: str) -> str | None:
    value = await session.scalar(select(SystemSetting.value).where(SystemSetting.key == key))
    return value.strip() if isinstance(value, str) and value.strip() else None


async def _get_image_runtime(session: AsyncSession) -> tuple[str, str, str, str]:
    provider = await _read_system_setting(session, "LLM_PROVIDER") or os.getenv("LLM_PROVIDER") or "openai"
    provider = provider.strip().lower()
    shared_model = await _read_system_setting(session, "IMAGE_MODEL") or os.getenv("IMAGE_MODEL") or ""

    if provider == "openrouter":
        api_key = await _read_system_setting(session, "OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        base_url = (
            await _read_system_setting(session, "OPENROUTER_BASE_URL")
            or os.getenv("OPENROUTER_BASE_URL")
            or OPENROUTER_IMAGE_BASE_URL
        )
        model = (
            shared_model
            or await _read_system_setting(session, "OPENROUTER_IMAGE_MODEL")
            or os.getenv("OPENROUTER_IMAGE_MODEL")
            or "google/gemini-3.1-flash-image-preview"
        )

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="OPENROUTER_API_KEY is not configured for illustration generation.",
            )

        return provider, api_key, base_url.rstrip("/"), model

    if provider == "openai":
        api_key = await _read_system_setting(session, "OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = await _read_system_setting(session, "OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL") or OPENAI_IMAGE_BASE_URL
        model = shared_model or await _read_system_setting(session, "OPENAI_IMAGE_MODEL") or os.getenv("OPENAI_IMAGE_MODEL") or OPENAI_IMAGE_MODEL

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="OPENAI_API_KEY is not configured for illustration generation.",
            )

        return provider, api_key, base_url.rstrip("/"), model

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Illustration provider '{provider}' is not supported yet.",
    )


def _decode_openrouter_data_url(image_url: str) -> tuple[bytes, str]:
    if not image_url.startswith("data:") or "," not in image_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenRouter did not return a valid image data URL.",
        )

    header, encoded = image_url.split(",", 1)
    mime_type = "image/png"
    if ";" in header:
        mime_type = header[5:].split(";", 1)[0] or mime_type
    return base64.b64decode(encoded), mime_type


def _build_illustration_prompt(item: ContentPlanItem) -> str:
    research_data = item.research_data if isinstance(item.research_data, dict) else {}
    generation_payload = research_data.get("generation_payload", {})
    if not isinstance(generation_payload, dict):
        generation_payload = {}

    asset_brief = research_data.get("asset_brief")
    if not isinstance(asset_brief, str) or not asset_brief.strip():
        asset_brief = generation_payload.get("asset_brief")
    if not isinstance(asset_brief, str):
        asset_brief = ""

    summary = generation_payload.get("summary")
    if not isinstance(summary, str):
        summary = ""

    channel_targets = research_data.get("channel_targets")
    if not isinstance(channel_targets, list):
        channel_targets = []
    previous_generated_image = research_data.get("generated_image")
    previous_prompt = ""
    if isinstance(previous_generated_image, dict):
        raw_previous_prompt = previous_generated_image.get("prompt")
        if isinstance(raw_previous_prompt, str):
            previous_prompt = raw_previous_prompt.strip()
    raw_variation_index = research_data.get("image_variation_index")
    variation_index = raw_variation_index if isinstance(raw_variation_index, int) and raw_variation_index > 0 else 0
    visual_directions = [
        "Use a medium shot with the character at a work desk and a clean editorial composition.",
        "Use a closer portrait crop with a clear facial expression and a softer background scene.",
        "Use an over-the-shoulder or angled composition that shows the character in action, not posing.",
        "Use a wider scene with the human character plus one supporting object or interface element tied to the topic.",
        "Use a more magazine-cover-like composition with stronger silhouette, gesture and focal lighting.",
    ]

    keywords = ", ".join(item.target_keywords[:6]) if item.target_keywords else "AI, automation, practical use"
    channel_hint = ", ".join(str(channel) for channel in channel_targets if channel) or "Telegram post"
    angle = item.angle or "Explain the value through a calm, practical and human example."

    brief = asset_brief.strip() or "Minimal editorial illustration with clear focal point, readable composition and clean background."
    summary_line = f"Context: {summary.strip()}" if summary.strip() else ""

    variation_instruction = ""
    if variation_index > 0:
        variation_style = visual_directions[(variation_index - 1) % len(visual_directions)]
        variation_instruction = (
            f"\nVariation request: create a noticeably different visual concept from previous attempts. "
            f"This is regeneration #{variation_index + 1}. Change composition, camera angle, scene setup or metaphor while keeping the same topic. "
            f"Preferred variation direction: {variation_style}"
        )
        if previous_prompt:
            variation_instruction += "\nDo not simply repeat this previous prompt direction:\n" + previous_prompt
    else:
        variation_instruction = f"\nPreferred variation direction: {visual_directions[0]}"

    return (
        "Create a high-quality editorial illustration for a Russian-language social post.\n"
        "Style: modern, clean, minimal, practical, calm, trustworthy, not hype, not futuristic cliche, no text in the image.\n"
        "Audience: non-technical entrepreneurs, experts and practitioners who are curious about AI but do not want complexity.\n"
        "The image must include one clear human character or persona as the main focal subject. "
        "Avoid abstract shapes, faceless symbolism and empty conceptual compositions.\n"
        "Show a real person, expert, founder, creator or professional in a readable scene with visible face, emotion and posture.\n"
        f"Primary channel: {channel_hint}.\n"
        f"Topic: {item.title}.\n"
        f"Angle: {angle}\n"
        f"Keywords: {keywords}.\n"
        f"Visual brief: {brief}\n"
        f"{summary_line}\n"
        f"{variation_instruction}\n"
        "The image should feel like a polished blog or Telegram cover illustration, square composition, strong focal object, subtle depth, soft neutral palette. "
        "Prefer a human-centered composition over abstract metaphors."
    ).strip()


async def generate_illustration_for_item(session: AsyncSession, item: ContentPlanItem) -> dict:
    provider, api_key, base_url, model = await _get_image_runtime(session)
    prompt = _build_illustration_prompt(item)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            if provider == "openrouter":
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        **headers,
                        "HTTP-Referer": "https://content.flowsmart.ru",
                        "X-OpenRouter-Title": "Athena Content",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "modalities": ["image", "text"],
                        "image_config": {
                            "aspect_ratio": "1:1",
                            "image_size": "1K",
                        },
                    },
                )
            else:
                response = await client.post(
                    f"{base_url}/images/generations",
                    headers=headers,
                    json={
                        "model": model,
                        "prompt": prompt,
                        "size": "1024x1024",
                    },
                )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Illustration generation request failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Illustration generation failed with status {response.status_code}.",
        )

    data = response.json()
    mime_type = "image/png"
    if provider == "openrouter":
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Illustration generation did not return OpenRouter choices.",
            )
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        images = message.get("images") if isinstance(message, dict) else None
        if not isinstance(images, list) or not images:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Illustration generation did not return OpenRouter image data.",
            )
        image_block = images[0] if isinstance(images[0], dict) else {}
        image_url_block = image_block.get("image_url") if isinstance(image_block, dict) else None
        image_url = image_url_block.get("url") if isinstance(image_url_block, dict) else None
        if not isinstance(image_url, str) or not image_url.strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Illustration generation did not return OpenRouter image bytes.",
            )
        image_bytes, mime_type = _decode_openrouter_data_url(image_url)
    else:
        image_records = data.get("data")
        if not isinstance(image_records, list) or not image_records:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Illustration generation did not return image data.",
            )

        image_payload = image_records[0]
        b64_json = image_payload.get("b64_json")
        if not isinstance(b64_json, str) or not b64_json.strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Illustration generation did not return image bytes.",
            )
        image_bytes = base64.b64decode(b64_json)

    MEDIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _purge_item_media_files(item, f"{item.id}-generated-*")
    file_name = f"{item.id}-generated-{int(datetime.now(timezone.utc).timestamp())}.png"
    file_path = MEDIA_OUTPUT_DIR / file_name
    file_path.write_bytes(image_bytes)

    research_data = dict(item.research_data) if isinstance(item.research_data, dict) else {}
    raw_variation_index = research_data.get("image_variation_index")
    variation_index = raw_variation_index if isinstance(raw_variation_index, int) and raw_variation_index >= 0 else 0
    generated_image = {
        "url": f"/api/media/{file_name}",
        "prompt": prompt,
        "model": model,
        "mime_type": mime_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "variation_index": variation_index,
    }
    prompt_history = research_data.get("generated_image_prompt_history")
    if not isinstance(prompt_history, list):
        prompt_history = []
    prompt_history = [*prompt_history[-4:], prompt]
    research_data["generated_image"] = generated_image
    research_data["generated_image_prompt_history"] = prompt_history
    research_data["image_variation_index"] = variation_index + 1
    item.research_data = research_data

    await session.commit()
    await session.refresh(item)
    return generated_image


async def save_uploaded_illustration_for_item(
    session: AsyncSession,
    item: ContentPlanItem,
    *,
    file_bytes: bytes,
    mime_type: str,
    original_file_name: str | None = None,
) -> dict:
    normalized_mime_type = mime_type.strip().lower()
    file_suffix = ALLOWED_UPLOAD_MIME_TYPES.get(normalized_mime_type)
    if not file_suffix:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Поддерживаются только PNG, JPG и WEBP.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл изображения пустой.",
        )

    if len(file_bytes) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Изображение слишком большое. Лимит: 15 MB.",
        )

    MEDIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _purge_item_media_files(item, f"{item.id}-uploaded-*")

    file_name = f"{item.id}-uploaded-{int(datetime.now(timezone.utc).timestamp())}{file_suffix}"
    file_path = MEDIA_OUTPUT_DIR / file_name
    file_path.write_bytes(file_bytes)

    research_data = dict(item.research_data) if isinstance(item.research_data, dict) else {}
    generated_image = {
        "url": f"/api/media/{file_name}",
        "prompt": "Uploaded by user",
        "model": "manual_upload",
        "mime_type": normalized_mime_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file_name": original_file_name or file_name,
    }
    research_data["generated_image"] = generated_image
    item.research_data = research_data

    await session.commit()
    await session.refresh(item)
    return generated_image
