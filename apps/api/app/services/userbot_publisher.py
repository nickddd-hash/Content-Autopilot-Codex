from __future__ import annotations

import os

from telethon import TelegramClient
from telethon.errors import FloodWaitError

from app.core.config import settings


def _resolve_entity(chat_id: str | int) -> int | str:
    """Convert numeric string chat_id to int so Telethon uses it directly without contact lookup."""
    if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
        return int(chat_id)
    return chat_id


async def publish_with_userbot(chat_id: str | int, text: str, image_path: str | None = None) -> None:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured.")

    os.makedirs(settings.telegram_session_dir, exist_ok=True)
    session_path = os.path.join(settings.telegram_session_dir, "userbot_session")
    entity = _resolve_entity(chat_id)

    try:
        async with TelegramClient(session_path, settings.telegram_api_id, settings.telegram_api_hash) as client:
            if image_path and os.path.exists(image_path):
                await client.send_file(entity, image_path, caption=text, parse_mode="html")
            else:
                await client.send_message(entity, text, parse_mode="html", link_preview=True)
    except FloodWaitError as exc:
        raise ValueError(f"Telegram flood wait: нужно подождать {exc.seconds} секунд перед следующей отправкой.") from exc
