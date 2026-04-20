from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product
from app.services.llm_client import LLMClientError, generate_json


def _join_lines(values: list[str]) -> str:
    if not values:
        return "not specified"
    return "\n".join(f"- {value}" for value in values)


def _build_fallback_plan_items(
    product: Product,
    plan: ContentPlan,
    num_items: int,
    theme_override: str | None = None,
) -> list[dict[str, Any]]:
    focus = theme_override or plan.theme or product.value_proposition or product.short_description or product.name
    audience = product.target_audience or "business owners and practitioners"
    pillars = [pillar for pillar in product.content_pillars if pillar]
    keywords = [keyword for keyword in (pillars[:2] or [product.name, "AI automation"]) if keyword]

    templates = [
        {
            "title": f"Как {focus} помогает убрать лишнюю ручную работу",
            "angle": f"Показать на понятных примерах, как {focus} снижает рутину и хаос для аудитории: {audience}.",
            "article_type": "educational",
        },
        {
            "title": f"5 ситуаций, где {focus} уже даёт практическую пользу",
            "angle": "Собрать простые прикладные сценарии без перегруза техническими деталями.",
            "article_type": "listicle",
        },
        {
            "title": f"Почему люди откладывают внедрение {focus} и что им мешает",
            "angle": "Разобрать страх, лень и ощущение сложности, которые мешают начать.",
            "article_type": "educational",
        },
        {
            "title": f"Как понять, что {focus} действительно нужен именно вам",
            "angle": "Дать критерии, по которым человек может увидеть реальную пользу в своей работе.",
            "article_type": "checklist",
        },
        {
            "title": f"Что выглядит как хайп вокруг {focus}, а что реально работает",
            "angle": "Сравнить пустые обещания и реальные рабочие сценарии.",
            "article_type": "comparison",
        },
        {
            "title": f"С чего начать {focus}, если не хочется разбираться в технологиях",
            "angle": "Показать мягкий вход для нетехнического человека через простые шаги и понятные задачи.",
            "article_type": "guide",
        },
        {
            "title": f"Как {focus} может помочь эксперту, практике или маленькому бизнесу",
            "angle": "Приземлить тему на повседневную работу специалистов и владельцев небольших проектов.",
            "article_type": "educational",
        },
        {
            "title": f"Какие задачи лучше всего отдавать {focus} в первую очередь",
            "angle": "Выделить задачи с быстрой отдачей и понятным результатом.",
            "article_type": "checklist",
        },
    ]

    items: list[dict[str, Any]] = []
    for index in range(num_items):
        template = templates[index % len(templates)]
        items.append(
            {
                "title": template["title"],
                "angle": template["angle"],
                "target_keywords": keywords,
                "article_type": template["article_type"],
                "cta_type": "soft",
            }
        )
    return items


def build_plan_generation_messages(
    product: Product,
    brand_profile: BrandProfile | None,
    plan: ContentPlan,
    num_items: int = 8,
    theme_override: str | None = None,
) -> list[dict[str, str]]:
    brand_name = brand_profile.brand_name if brand_profile and brand_profile.brand_name else product.name
    brand_summary = (
        brand_profile.brand_summary
        if brand_profile and brand_profile.brand_summary
        else product.short_description or product.value_proposition or "No brand summary provided."
    )
    audience_notes = brand_profile.audience_notes if brand_profile else []
    core_messages = brand_profile.core_messages if brand_profile else []

    system_prompt = f"""
You are a senior content strategist for a personal content autopilot.
Your job is to generate a list of {num_items} structured content plan items for a given month and theme.
Focus on creating high-signal, practical, and engaging topics that align with the brand and product.
Do not return generic or filler ideas. Make sure topics naturally progress throughout the month.

Return valid JSON with this exact shape:
{{
  "items": [
    {{
      "title": "string",
      "angle": "string",
      "target_keywords": ["string", "string"],
      "article_type": "string (e.g. educational, checklist, comparison)",
      "cta_type": "string (e.g. soft, hard, none)"
    }}
  ]
}}
""".strip()

    user_prompt = f"""
Product name: {product.name}
Brand name: {brand_name}
Category: {product.category or "not specified"}
Lifecycle stage: {product.lifecycle_stage or "not specified"}

Brand summary:
{brand_summary}

Target audience:
{product.target_audience or "not specified"}

Audience segments:
{_join_lines(product.audience_segments)}

Pain points:
{_join_lines(product.pain_points)}

Value proposition:
{product.value_proposition or "not specified"}

Content pillars:
{_join_lines(product.content_pillars)}

Brand audience notes:
{_join_lines(audience_notes)}

Core messages:
{_join_lines(core_messages)}

Plan month: {plan.month}
Plan theme: {theme_override or plan.theme or "General"}

Please generate {num_items} distinct content plan items that fit this theme.
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def generate_plan_items_for_plan(
    session: AsyncSession,
    plan_id: uuid.UUID,
    theme_override: str | None = None,
    num_items_override: int | None = None,
) -> list[ContentPlanItem]:
    plan_statement = (
        select(ContentPlan)
        .where(ContentPlan.id == plan_id)
        .options(selectinload(ContentPlan.product).selectinload(Product.content_settings))
        .options(selectinload(ContentPlan.items))
    )
    plan = await session.scalar(plan_statement)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found")

    brand_profile = await session.scalar(select(BrandProfile).limit(1))

    # Calculate how many items to generate
    settings = plan.product.content_settings
    num_items = num_items_override or (settings.articles_per_month if settings else 4)

    messages = build_plan_generation_messages(
        plan.product,
        brand_profile,
        plan,
        num_items,
        theme_override=theme_override,
    )

    try:
        response_data = await generate_json(messages, session=session)
        items_data = response_data.get("items", [])
        if not isinstance(items_data, list):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM returned invalid format")
    except LLMClientError:
        items_data = _build_fallback_plan_items(
            plan.product,
            plan,
            num_items,
            theme_override=theme_override,
        )

    starting_order = max([item.order for item in plan.items], default=0)
    
    new_items = []
    for i, data in enumerate(items_data):
        if not isinstance(data, dict):
            continue

        raw_keywords = data.get("target_keywords", [])
        target_keywords = raw_keywords if isinstance(raw_keywords, list) else []

        item = ContentPlanItem(
            plan_id=plan.id,
            order=starting_order + i + 1,
            title=str(data.get("title") or f"Generated Item {i+1}"),
            angle=str(data.get("angle") or ""),
            target_keywords=[str(keyword) for keyword in target_keywords if keyword],
            article_type=str(data.get("article_type") or "educational"),
            cta_type=str(data.get("cta_type") or "soft"),
            status="planned"
        )
        session.add(item)
        new_items.append(item)

    if not new_items:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned no usable plan items.",
        )

    await session.commit()
    for item in new_items:
        await session.refresh(item)
        
    return new_items


# ── Rewrite Mode: generate plan items from IngestedContent ─────────────────────

async def generate_rewrite_items_from_ingested(
    session: AsyncSession,
    plan_id: uuid.UUID,
    ingested_content_ids: list[uuid.UUID],
) -> list[ContentPlanItem]:
    """
    Takes a list of IngestedContent IDs and creates ContentPlanItems
    with the 'rewrite' angle pre-filled — so the AI uses viral competitor
    content as the creative brief.
    """
    from app.models.monitoring import IngestedContent  # avoid circular import

    plan_statement = (
        select(ContentPlan)
        .where(ContentPlan.id == plan_id)
        .options(selectinload(ContentPlan.product).selectinload(Product.content_settings))
        .options(selectinload(ContentPlan.items))
    )
    plan = await session.scalar(plan_statement)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found")

    ingested_result = await session.execute(
        select(IngestedContent).where(IngestedContent.id.in_(ingested_content_ids))
    )
    ingested_items = list(ingested_result.scalars().all())

    if not ingested_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ingested content found for given IDs")

    starting_order = max((item.order for item in plan.items), default=0)
    brand_profile = await session.scalar(select(BrandProfile).limit(1))
    brand_name = brand_profile.brand_name if brand_profile and brand_profile.brand_name else plan.product.name

    new_items: list[ContentPlanItem] = []

    for i, ingested in enumerate(ingested_items):
        angle = (
            f"Rewrite & adapt this viral {ingested.platform} content for {brand_name}: "
            f"\"{(ingested.text_content or '')[:300]}\" "
            f"(engagement score: {ingested.engagement_score:.0%})"
        )
        item = ContentPlanItem(
            plan_id=plan.id,
            order=starting_order + i + 1,
            title=f"[Rewrite] {ingested.platform.capitalize()} Viral Content #{i + 1}",
            angle=angle,
            target_keywords=[],
            article_type="rewrite",
            cta_type="soft",
            status="planned",
            research_data={"ingested_content_id": str(ingested.id), "raw": ingested.raw_data},
        )
        session.add(item)
        new_items.append(item)

        # Mark source as processed
        ingested.is_processed = True

    await session.commit()
    for item in new_items:
        await session.refresh(item)

    return new_items
