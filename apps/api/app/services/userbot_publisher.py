from __future__ import annotations

import os

from telethon import TelegramClient

from app.core.config import settings


async def publish_with_userbot(chat_id: str | int, text: str, image_path: str | None = None) -> None:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured.")

    os.makedirs(settings.telegram_session_dir, exist_ok=True)
    session_path = os.path.join(settings.telegram_session_dir, "userbot_session")

    async with TelegramClient(session_path, settings.telegram_api_id, settings.telegram_api_hash) as client:
        if image_path and os.path.exists(image_path):
            await client.send_file(chat_id, image_path, caption=text, parse_mode="html")
        else:
            await client.send_message(chat_id, text, parse_mode="html", link_preview=True)
