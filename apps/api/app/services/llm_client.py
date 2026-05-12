from __future__ import annotations

import json
import os
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.system import SystemSetting

OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


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
            or "google/gemini-flash-1.5"
        )

        if not api_key.strip():
            raise LLMClientError("OPENROUTER_API_KEY is not configured.")

        return provider, api_key.strip(), base_url.rstrip("/"), model.strip()

    if provider == "google":
        api_key = (await _read_system_setting(session, "GOOGLE_API_KEY")) or settings.google_api_key or os.getenv("GOOGLE_API_KEY") or ""
        base_url = (await _read_system_setting(session, "GOOGLE_BASE_URL")) or os.getenv("GOOGLE_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta"
        model = shared_model or (await _read_system_setting(session, "GOOGLE_MODEL")) or os.getenv("GOOGLE_MODEL") or "gemini-2.0-flash-exp"

        if not api_key.strip():
            raise LLMClientError("GOOGLE_API_KEY is not configured.")

        return provider, api_key.strip(), base_url.rstrip("/"), model.strip()

    if provider == "agent":
        return "agent", "", "http://localhost:8001", "agent-model"

    raise LLMClientError(f"Unsupported LLM provider: {provider}")


def _extract_text_from_response(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content

    raise LLMClientError("LLM returned no text output.")


def _extract_google_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates")
    if isinstance(candidates, list) and candidates:
        first_candidate = candidates[0]
        content = first_candidate.get("content")
        if isinstance(content, dict):
            parts = content.get("parts")
            if isinstance(parts, list) and parts:
                text = parts[0].get("text")
                if isinstance(text, str) and text.strip():
                    return text

    raise LLMClientError("Google Gemini returned no text output.")


async def generate_json(messages: list[dict[str, str]], session: AsyncSession | None = None) -> dict[str, Any]:
    provider, api_key, base_url, model = await _resolve_runtime_config(session)

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            if provider == "openrouter":
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://content.flowsmart.ru",
                        "X-OpenRouter-Title": "Athena Content",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                    },
                )
            elif provider == "google":
                # Convert OpenAI messages to Gemini contents
                gemini_contents = []
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
                
                response = await client.post(
                    f"{base_url}/models/{model}:generateContent?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": gemini_contents,
                        "generationConfig": {
                            "response_mime_type": "application/json",
                        }
                    },
                )
            elif provider == "agent":
                response = await client.post(
                    f"{base_url}/generate-text",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": messages,
                    },
                )
            else:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                    },
                )
            response.raise_for_status()
        except httpx.HTTPError as error:
            # Try to extract error detail from Gemini
            detail = ""
            if error.response:
                try:
                    detail = f" | Detail: {error.response.text}"
                except:
                    pass
            raise LLMClientError(f"LLM request failed: {error}{detail}") from error

    payload = response.json()
    if provider == "google":
        text = _extract_google_text(payload)
    else:
        text = _extract_text_from_response(payload)
    
    try:
        # Attempt standard JSON parse
        return json.loads(text)
    except json.JSONDecodeError:
        # If it fails, try to extract the JSON block from conversational filler
        try:
            start_index = text.find('{')
            end_index = text.rfind('}')
            if start_index != -1 and end_index != -1:
                json_str = text[start_index : end_index + 1]
                return json.loads(json_str)
        except Exception:
            pass
        raise LLMClientError(f"LLM returned invalid JSON: {text[:200]}") from None
