from __future__ import annotations

from typing import Any

import httpx


class ChannelValidationError(Exception):
    pass


def _friendly_http_error(platform: str, error: httpx.HTTPError) -> str:
    response = getattr(error, "response", None)
    status_code = response.status_code if response is not None else None

    if platform == "telegram":
        if status_code in {401, 404}:
            return "Telegram не принял bot token или chat_id. Проверьте данные и попробуйте снова."
        return "Не удалось проверить Telegram. Проверьте bot token, chat_id и права бота в канале."

    if platform == "vk":
        if status_code in {401, 403, 404}:
            return "VK не принял access token или group_id. Проверьте данные и попробуйте снова."
        return "Не удалось проверить VK. Проверьте access token и group_id."

    return f"Не удалось проверить {platform}."


async def validate_channel_connection(platform: str, secrets: dict[str, Any], settings: dict[str, Any]) -> tuple[str | None, str | None]:
    normalized_platform = platform.strip().lower()

    if normalized_platform == "telegram":
        bot_token = str(secrets.get("bot_token", "")).strip()
        chat_id = str(settings.get("chat_id", "")).strip()
        if not bot_token or not chat_id:
            raise ChannelValidationError("Для Telegram нужны bot_token и chat_id.")

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                me_response = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                me_response.raise_for_status()
                me_payload = me_response.json()
                if not me_payload.get("ok"):
                    raise ChannelValidationError("Telegram bot token не прошёл проверку.")

                chat_response = await client.get(
                    f"https://api.telegram.org/bot{bot_token}/getChat",
                    params={"chat_id": chat_id},
                )
                chat_response.raise_for_status()
                chat_payload = chat_response.json()
                if not chat_payload.get("ok"):
                    raise ChannelValidationError("Не удалось получить Telegram chat по указанному chat_id.")
        except httpx.HTTPError as error:
            raise ChannelValidationError(_friendly_http_error("telegram", error)) from error

        bot_username = me_payload.get("result", {}).get("username")
        chat_title = chat_payload.get("result", {}).get("title") or chat_payload.get("result", {}).get("username")
        return str(chat_id), chat_title or (f"@{bot_username}" if bot_username else "Telegram channel")

    if normalized_platform == "vk":
        access_token = str(secrets.get("access_token", "")).strip()
        group_id = str(settings.get("group_id", "")).strip()
        if not access_token or not group_id:
            raise ChannelValidationError("Для VK нужны access_token и group_id.")

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    "https://api.vk.com/method/groups.getById",
                    params={
                        "group_id": group_id,
                        "access_token": access_token,
                        "v": "5.199",
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as error:
            raise ChannelValidationError(_friendly_http_error("vk", error)) from error

        if payload.get("error"):
            raise ChannelValidationError("VK access token или group_id не прошли проверку.")

        group = (payload.get("response") or [{}])[0]
        resolved_group_id = group.get("id")
        resolved_name = group.get("name")
        return str(resolved_group_id) if resolved_group_id is not None else group_id, resolved_name or "VK group"

    raise ChannelValidationError(f"Платформа {platform} пока не поддерживается для автопостинга.")
