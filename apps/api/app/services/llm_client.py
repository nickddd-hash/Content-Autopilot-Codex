from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import SystemSetting

OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-5.4-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
HUBRIS_BASE_URL = "https://api.hubris.pw/v1"


class LLMClientError(Exception):
    pass


async def _read_system_setting(session: AsyncSession | None, key: str) -> str | None:
    if session is None:
        return None
    return await session.scalar(select(SystemSetting.value).where(SystemSetting.key == key))


async def _resolve_runtime_config(session: AsyncSession | None) -> tuple[str, str, str, str]:
    provider = (await _read_system_setting(session, "LLM_PROVIDER")) or os.getenv("LLM_PROVIDER") or "openai"
    provider = provider.strip().lower()
    shared_model = (await _read_system_setting(session, "TEXT_MODEL")) or os.getenv("TEXT_MODEL") or ""

    if provider == "openai":
        api_key = (await _read_system_setting(session, "OPENAI_API_KEY")) or os.getenv("OPENAI_API_KEY") or ""
        base_url = (await _read_system_setting(session, "OPENAI_BASE_URL")) or os.getenv("OPENAI_BASE_URL") or OPENAI_BASE_URL
        model = shared_model or (await _read_system_setting(session, "OPENAI_MODEL")) or os.getenv("OPENAI_MODEL") or OPENAI_MODEL

        if not api_key.strip():
            raise LLMClientError("OPENAI_API_KEY is not configured.")

        return provider, api_key.strip(), base_url.rstrip("/"), model.strip()

    if provider == "openrouter":
        api_key = (await _read_system_setting(session, "OPENROUTER_API_KEY")) or os.getenv("OPENROUTER_API_KEY") or ""
        base_url = (await _read_system_setting(session, "OPENROUTER_BASE_URL")) or os.getenv("OPENROUTER_BASE_URL") or OPENROUTER_BASE_URL
        model = (
            shared_model
            or (await _read_system_setting(session, "OPENROUTER_MODEL"))
            or os.getenv("OPENROUTER_MODEL")
            or "google/gemini-2.5-flash"
        )

        if not api_key.strip():
            raise LLMClientError("OPENROUTER_API_KEY is not configured.")

        return provider, api_key.strip(), base_url.rstrip("/"), model.strip()

    if provider == "hubris":
        api_key = (await _read_system_setting(session, "HUBRIS_API_KEY")) or os.getenv("HUBRIS_API_KEY") or ""
        base_url = HUBRIS_BASE_URL
        model = (
            shared_model
            or (await _read_system_setting(session, "HUBRIS_MODEL"))
            or os.getenv("HUBRIS_MODEL")
            or "google/gemini-2.5-flash"
        )

        if not api_key.strip():
            raise LLMClientError("HUBRIS_API_KEY is not configured.")

        return provider, api_key.strip(), base_url.rstrip("/"), model.strip()

    raise LLMClientError(f"Unsupported LLM provider: {provider}")


def _extract_text_from_response(payload: dict[str, Any]) -> str:
    output = payload.get("output")
    if isinstance(output, list):
        collected: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    text = block.get("text")
                    if isinstance(text, str):
                        collected.append(text)
        if collected:
            return "\n".join(collected)

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    raise LLMClientError("LLM returned no text output.")


def _extract_openrouter_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content

    raise LLMClientError("OpenRouter returned no text output.")


async def generate_json(messages: list[dict[str, str]], session: AsyncSession | None = None) -> dict[str, Any]:
    provider, api_key, base_url, model = await _resolve_runtime_config(session)

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            if provider in ("openrouter", "hubris"):
                headers: dict[str, str] = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                if provider == "openrouter":
                    headers["HTTP-Referer"] = "https://content.flowsmart.ru"
                    headers["X-OpenRouter-Title"] = "Athena Content"
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                    },
                )
            else:
                response = await client.post(
                    f"{base_url}/responses",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "input": messages,
                        "text": {"format": {"type": "json_object"}},
                    },
                )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise LLMClientError(f"LLM request failed: {error}") from error

    payload = response.json()
    text = _extract_openrouter_text(payload) if provider in ("openrouter", "hubris") else _extract_text_from_response(payload)
    text = _strip_code_fences(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise LLMClientError("LLM returned invalid JSON.") from error


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()
