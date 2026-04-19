from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.system import SystemSetting


class LLMClientError(RuntimeError):
    """Raised when the LLM client fails to produce a usable response."""


@dataclass(slots=True)
class RuntimeLLMSettings:
    provider: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    gemini_api_key: str
    gemini_model: str
    gemini_base_url: str
    kie_api_key: str
    kie_model: str
    kie_base_url: str
    app_base_url: str
    app_name: str


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMClientError("LLM response was not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise LLMClientError("LLM response JSON was not an object.")

    return payload


def _extract_openai_content(data: dict[str, Any], provider_name: str) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMClientError(f"{provider_name} response did not include message content.") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMClientError(f"{provider_name} returned empty content.")

    return content


def _extract_kie_content(data: dict[str, Any]) -> str:
    outputs = data.get("output", [])
    if not isinstance(outputs, list):
        raise LLMClientError("KIE response did not include output.")

    for output in outputs:
        if output.get("type") != "message":
            continue
        for content in output.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text

    raise LLMClientError("KIE response did not include output_text.")


def _messages_to_gemini_prompt(messages: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for message in messages:
        role = message.get("role", "user").upper()
        content = message.get("content", "")
        parts.append(f"{role}:\n{content}")
    return "\n\n".join(parts)


async def _load_system_settings(session: AsyncSession | None) -> dict[str, str]:
    if session is None:
        return {}

    result = await session.execute(select(SystemSetting))
    return {
        row.key: row.value
        for row in result.scalars().all()
        if row.value is not None
    }


async def _get_runtime_settings(session: AsyncSession | None) -> RuntimeLLMSettings:
    system_settings = await _load_system_settings(session)

    provider = (system_settings.get("LLM_PROVIDER") or settings.llm_provider or "").strip().lower()
    openrouter_api_key = system_settings.get("OPENROUTER_API_KEY") or settings.openrouter_api_key
    openrouter_model = system_settings.get("OPENROUTER_MODEL") or settings.openrouter_model
    openai_api_key = system_settings.get("OPENAI_API_KEY") or settings.openai_api_key
    openai_model = system_settings.get("OPENAI_MODEL") or settings.openai_model
    gemini_api_key = system_settings.get("GEMINI_API_KEY") or settings.gemini_api_key
    gemini_model = system_settings.get("GEMINI_MODEL") or settings.gemini_model
    kie_api_key = system_settings.get("KIE_AI_API_KEY") or ""
    kie_model = system_settings.get("KIE_MODEL") or "gpt-5-4"
    kie_base_url = system_settings.get("KIE_BASE_URL") or "https://api.kie.ai/codex/v1"

    if provider in {"", "fallback"}:
        if kie_api_key:
            provider = "kie"
        elif openrouter_api_key:
            provider = "openrouter"
        elif openai_api_key:
            provider = "openai"
        elif gemini_api_key:
            provider = "gemini"
        else:
            provider = "fallback"

    return RuntimeLLMSettings(
        provider=provider,
        openrouter_api_key=openrouter_api_key,
        openrouter_model=openrouter_model,
        openrouter_base_url=settings.openrouter_base_url,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=settings.openai_base_url,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_base_url=settings.gemini_base_url,
        kie_api_key=kie_api_key,
        kie_model=kie_model,
        kie_base_url=kie_base_url.rstrip("/"),
        app_base_url=settings.app_base_url,
        app_name=settings.app_name,
    )


async def _generate_via_openrouter(
    messages: list[dict[str, str]],
    runtime: RuntimeLLMSettings,
) -> dict[str, Any]:
    if not runtime.openrouter_api_key:
        raise LLMClientError("OpenRouter API key is not configured.")

    headers = {
        "Authorization": f"Bearer {runtime.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": runtime.app_base_url,
        "X-Title": runtime.app_name,
    }
    payload = {
        "model": runtime.openrouter_model,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{runtime.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(f"OpenRouter request failed with status {response.status_code}.")

    data = response.json()
    content = _extract_openai_content(data, "OpenRouter")
    return _extract_json_payload(content)


async def _generate_via_openai(
    messages: list[dict[str, str]],
    runtime: RuntimeLLMSettings,
) -> dict[str, Any]:
    if not runtime.openai_api_key:
        raise LLMClientError("OpenAI API key is not configured.")

    headers = {
        "Authorization": f"Bearer {runtime.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": runtime.openai_model,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{runtime.openai_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(f"OpenAI request failed with status {response.status_code}.")

    data = response.json()
    content = _extract_openai_content(data, "OpenAI")
    return _extract_json_payload(content)


async def _generate_via_gemini(
    messages: list[dict[str, str]],
    runtime: RuntimeLLMSettings,
) -> dict[str, Any]:
    if not runtime.gemini_api_key:
        raise LLMClientError("Gemini API key is not configured.")

    prompt = _messages_to_gemini_prompt(messages)
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{runtime.gemini_base_url}/models/{runtime.gemini_model}:generateContent",
            params={"key": runtime.gemini_api_key},
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(f"Gemini request failed with status {response.status_code}.")

    data = response.json()
    try:
        content = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMClientError("Gemini response did not include text content.") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMClientError("Gemini returned empty content.")

    return _extract_json_payload(content)


async def _generate_via_kie(
    messages: list[dict[str, str]],
    runtime: RuntimeLLMSettings,
) -> dict[str, Any]:
    if not runtime.kie_api_key:
        raise LLMClientError("KIE API key is not configured.")

    payload = {
        "model": runtime.kie_model,
        "stream": False,
        "input": [
            {
                "role": message.get("role", "user"),
                "content": [
                    {
                        "type": "input_text",
                        "text": message.get("content", ""),
                    }
                ],
            }
            for message in messages
        ],
    }
    headers = {
        "Authorization": f"Bearer {runtime.kie_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{runtime.kie_base_url}/responses",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(f"KIE request failed with status {response.status_code}.")

    data = response.json()
    content = _extract_kie_content(data)
    return _extract_json_payload(content)


async def generate_json(
    messages: list[dict[str, str]],
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    runtime = await _get_runtime_settings(session)
    provider = runtime.provider

    if provider == "openrouter":
        return await _generate_via_openrouter(messages, runtime)
    if provider == "openai":
        return await _generate_via_openai(messages, runtime)
    if provider == "gemini":
        return await _generate_via_gemini(messages, runtime)
    if provider == "kie":
        return await _generate_via_kie(messages, runtime)
    if provider == "fallback":
        raise LLMClientError("LLM provider is set to fallback and no runtime API key was found.")

    raise LLMClientError(f"Unsupported LLM provider: {provider}")
