from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluator import ContentEvaluator, ContentEvaluationResult
from app.models.content_plan import ContentPlanItem
from app.services.llm_client import generate_json

logger = logging.getLogger(__name__)


async def evaluate_item_theme(session: AsyncSession, item_id: uuid.UUID) -> list[ContentEvaluationResult]:
    """Evaluates just the title and angle before generation."""
    item = await session.get(ContentPlanItem, item_id)
    if not item: return []

    evaluators = (await session.execute(select(ContentEvaluator).where(ContentEvaluator.is_active == True))).scalars().all()
    
    results = []
    for evaluator in evaluators:
        try:
            system_prompt = (
                f"{evaluator.system_prompt}\n\n"
                "Твоя задача — оценить ИДЕЮ поста (заголовок и угол подачи).\n"
                "Оценивай по 10-балльной шкале насколько тема интересна, не банальна и подходит стратегии.\n"
                "Верни JSON: {score: int, feedback: string, metrics: {originality: int, relevance: int}}"
            )
            user_prompt = f"Заголовок: {item.title}\nУгол подачи: {item.angle or 'не задан'}"

            payload = await generate_json([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], session=session)

            result = ContentEvaluationResult(
                content_plan_item_id=item.id,
                evaluator_id=evaluator.id,
                score=payload.get("score", 0),
                feedback_text=f"[ТЕМА] {payload.get('feedback', '')}",
                metrics_json={**payload.get("metrics", {}), "stage": "theme"},
            )
            session.add(result)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed theme eval: {e}")
    await session.commit()
    return results


async def evaluate_item_content(session: AsyncSession, item_id: uuid.UUID) -> list[ContentEvaluationResult]:
    """Evaluates the full generated post for readability and impact."""
    item = await session.get(ContentPlanItem, item_id)
    if not item: return []

    evaluators = (await session.execute(select(ContentEvaluator).where(ContentEvaluator.is_active == True))).scalars().all()
    
    research_data = item.research_data or {}
    generation_payload = research_data.get("generation_payload", {})
    content_text = generation_payload.get("draft_markdown", "")
    
    if not content_text: return []

    results = []
    for evaluator in evaluators:
        try:
            system_prompt = (
                f"{evaluator.system_prompt}\n\n"
                "Твоя задача — оценить ТЕКСТ готового поста.\n"
                "Критерии: читабельность, отсутствие канцеляризмов, легкость восприятия, польза.\n"
                "Верни JSON: {score: int, feedback: string, metrics: {readability: int, impact: int}}"
            )
            user_prompt = f"Текст поста:\n\n{content_text}"

            payload = await generate_json([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], session=session)

            result = ContentEvaluationResult(
                content_plan_item_id=item.id,
                evaluator_id=evaluator.id,
                score=payload.get("score", 0),
                feedback_text=f"[КОНТЕНТ] {payload.get('feedback', '')}",
                metrics_json={**payload.get("metrics", {}), "stage": "content"},
            )
            session.add(result)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed content eval: {e}")
    await session.commit()
    return results
