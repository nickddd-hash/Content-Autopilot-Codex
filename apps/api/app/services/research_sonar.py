from __future__ import annotations

import os

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_client import LLMClientError, _read_system_setting

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SONAR_MODEL = "perplexity/sonar"

_DIRECTION_QUERIES: dict[str, str] = {
    "practical": (
        "реальные кейсы автоматизации с помощью ИИ для малого бизнеса и фрилансеров: "
        "конкретные примеры внедрений, задачи которые автоматизировали, результаты в цифрах. "
        "Тема: {topic}{angle}"
    ),
    "educational": (
        "актуальные объяснения и факты по теме: {topic}{angle}. "
        "Что нового в 2025-2026, как это работает на практике, конкретные примеры применения."
    ),
    "news": (
        "последние новости и анонсы по теме: {topic}{angle}. "
        "Свежие события, релизы, обновления инструментов ИИ за 2025-2026."
    ),
    "opinion": (
        "дискуссии, мнения экспертов и предпринимателей по теме: {topic}{angle}. "
        "Разные точки зрения, аргументы за и против, реальный опыт."
    ),
    "critical": (
        "реальные проблемы, ограничения и провалы ИИ по теме: {topic}{angle}. "
        "Завышенные ожидания, случаи когда не сработало, честные отзывы."
    ),
}


async def _get_openrouter_key(session: AsyncSession | None) -> str:
    key = (await _read_system_setting(session, "OPENROUTER_API_KEY")) or os.getenv("OPENROUTER_API_KEY") or ""
    if not key.strip():
        raise LLMClientError("OPENROUTER_API_KEY is not configured.")
    return key.strip()


def _build_query(topic: str, angle: str | None, direction: str) -> str:
    template = _DIRECTION_QUERIES.get(direction, _DIRECTION_QUERIES["practical"])
    angle_part = f", угол: {angle}" if angle else ""
    return template.format(topic=topic, angle=angle_part)


async def _call_sonar(query: str, session: AsyncSession | None) -> str:
    api_key = await _get_openrouter_key(session)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://content.flowsmart.ru",
                    "X-OpenRouter-Title": "Athena Content Research",
                },
                json={
                    "model": SONAR_MODEL,
                    "messages": [{"role": "user", "content": query}],
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise LLMClientError(f"Sonar request failed: {error}") from error

    payload = response.json()
    choices = payload.get("choices") or []
    if choices and isinstance(choices[0], dict):
        content = choices[0].get("message", {}).get("content", "")
        if content:
            return content.strip()

    raise LLMClientError("Sonar returned no content.")


async def run_sonar_research(
    topic: str,
    angle: str | None,
    direction: str,
    session: AsyncSession | None,
) -> str:
    """Initial mandatory research call. Returns empty string on failure — non-fatal."""
    try:
        query = _build_query(topic, angle, direction)
        return await _call_sonar(query, session)
    except LLMClientError:
        return ""


async def run_sonar_followup(followup_query: str, session: AsyncSession | None) -> str:
    """Model-requested follow-up research call. Returns empty string on failure."""
    try:
        return await _call_sonar(followup_query, session)
    except LLMClientError:
        return ""
