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


def build_plan_generation_messages(
    product: Product,
    brand_profile: BrandProfile | None,
    plan: ContentPlan,
    num_items: int = 8,
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
Plan theme: {plan.theme or "General"}

Please generate {num_items} distinct content plan items that fit this theme.
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def generate_plan_items_for_plan(session: AsyncSession, plan_id: uuid.UUID) -> list[ContentPlanItem]:
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
    num_items = settings.articles_per_month if settings else 4

    messages = build_plan_generation_messages(plan.product, brand_profile, plan, num_items)

    try:
        response_data = await generate_json(messages)
    except LLMClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    items_data = response_data.get("items", [])
    if not isinstance(items_data, list):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM returned invalid format")

    starting_order = max([item.order for item in plan.items], default=0)
    
    new_items = []
    for i, data in enumerate(items_data):
        item = ContentPlanItem(
            plan_id=plan.id,
            product_id=plan.product_id,
            order=starting_order + i + 1,
            title=data.get("title", f"Generated Item {i+1}"),
            angle=data.get("angle", ""),
            target_keywords=data.get("target_keywords", []),
            article_type=data.get("article_type", "educational"),
            cta_type=data.get("cta_type", "soft"),
            status="planned"
        )
        session.add(item)
        new_items.append(item)

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
            product_id=plan.product_id,
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

