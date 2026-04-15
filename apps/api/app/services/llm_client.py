from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings


class LLMClientError(RuntimeError):
    """Raised when the LLM client fails to produce a usable response."""


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


async def _generate_via_openrouter(messages: list[dict[str, str]]) -> dict[str, Any]:
    if not settings.openrouter_api_key:
        raise LLMClientError("OpenRouter API key is not configured.")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.app_base_url,
        "X-Title": settings.app_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(f"OpenRouter request failed with status {response.status_code}.")

    data = response.json()
    content = _extract_openai_content(data, "OpenRouter")
    return _extract_json_payload(content)


async def _generate_via_openai(messages: list[dict[str, str]]) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise LLMClientError("OpenAI API key is not configured.")

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        raise LLMClientError(f"OpenAI request failed with status {response.status_code}.")

    data = response.json()
    content = _extract_openai_content(data, "OpenAI")
    return _extract_json_payload(content)


def _messages_to_gemini_prompt(messages: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for message in messages:
        role = message.get("role", "user").upper()
        content = message.get("content", "")
        parts.append(f"{role}:\n{content}")
    return "\n\n".join(parts)


async def _generate_via_gemini(messages: list[dict[str, str]]) -> dict[str, Any]:
    if not settings.gemini_api_key:
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
            f"{settings.gemini_base_url}/models/{settings.gemini_model}:generateContent",
            params={"key": settings.gemini_api_key},
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


async def generate_json(messages: list[dict[str, str]]) -> dict[str, Any]:
    provider = settings.llm_provider.strip().lower()

    if provider == "openrouter":
        return await _generate_via_openrouter(messages)
    if provider == "openai":
        return await _generate_via_openai(messages)
    if provider == "gemini":
        return await _generate_via_gemini(messages)
    if provider == "fallback":
        raise LLMClientError("LLM provider is set to fallback.")

    raise LLMClientError(f"Unsupported LLM provider: {settings.llm_provider}")
