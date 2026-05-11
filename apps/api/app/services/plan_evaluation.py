from __future__ import annotations

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.evaluator import ContentEvaluator, ContentPlanAudit
from app.models.content_plan import ContentPlan, ContentPlanItem
from app.services.llm_client import generate_json

logger = logging.getLogger(__name__)


async def evaluate_plan_strategy(session: AsyncSession, plan_id: uuid.UUID) -> list[ContentPlanAudit]:
    plan = await session.get(
        ContentPlan, 
        plan_id,
        options=[selectinload(ContentPlan.items)]
    )
    if not plan:
        return []

    evaluators_result = await session.execute(select(ContentEvaluator).where(ContentEvaluator.is_active == True))
    evaluators = list(evaluators_result.scalars().all())
    if not evaluators:
        return []

    # Prepare plan summary for the LLM
    items_summary = []
    for item in sorted(plan.items, key=lambda x: x.order):
        items_summary.append(
            f"#{item.order + 1}. {item.title}\n"
            f"   Тип: {item.article_type}, Угол: {item.angle or 'не задан'}"
        )
    
    plan_text = "\n\n".join(items_summary)
    month_label = plan.month
    theme = plan.theme or "Общая тематика"

    results = []
    for evaluator in evaluators:
        try:
            # Check if audit already exists for this version (optional: could just overwrite)
            # For now, we'll just create a new one each time to have history or update the latest.
            
            system_prompt = (
                f"{evaluator.system_prompt}\n\n"
                "Твоя задача — провести аудит контент-плана на целый месяц.\n"
                "Оценивай структуру, разнообразие тем, логику повествования и то, насколько этот план будет тебе интересен в течение месяца.\n"
                "Верни ответ строго в формате JSON с полями:\n"
                "- score (int): общая оценка стратегии от 1 до 10\n"
                "- feedback (string): развернутый аудит (3-5 предложений)\n"
                "- metrics (dict): оценки по критериям (от 1 до 10):\n"
                "  - variety: разнообразие тем и форматов\n"
                "  - consistency: логическая связь между постами\n"
                "  - value: общая ценность контента для тебя"
            )
            user_prompt = (
                f"Контент-план на {month_label}\n"
                f"Основная тема: {theme}\n\n"
                f"Список постов:\n\n{plan_text}"
            )

            payload = await generate_json(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                session=session,
            )

            audit = ContentPlanAudit(
                plan_id=plan.id,
                evaluator_id=evaluator.id,
                score=payload.get("score", 0),
                feedback_text=payload.get("feedback", ""),
                metrics_json=payload.get("metrics", {}),
            )
            session.add(audit)
            results.append(audit)
            logger.info(f"Audited plan {plan.id} with {evaluator.role_key}: score {audit.score}")
        except Exception as e:
            logger.error(f"Failed to audit plan {plan.id} with evaluator {evaluator.role_key}: {e}")

    await session.commit()
    return results
