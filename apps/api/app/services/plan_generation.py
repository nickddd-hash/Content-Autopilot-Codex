from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product
from app.services.llm_client import LLMClientError, generate_json


def _join_lines(values: list[str]) -> str:
    if not values:
        return "not specified"
    return "\n".join(f"- {value}" for value in values)


def _get_active_channel_platforms(product: Product) -> list[str]:
    platforms: list[str] = []

    for channel in getattr(product, "channels", []) or []:
        if not getattr(channel, "is_active", True):
            continue
        platform = (getattr(channel, "platform", "") or "").strip().lower()
        if platform and platform not in platforms:
            platforms.append(platform)

    for channel in (product.primary_channels or []):
        platform = (channel or "").strip().lower()
        if platform and platform not in platforms:
            platforms.append(platform)

    return platforms


def _build_channel_strategy_notes(product: Product) -> str:
    platforms = _get_active_channel_platforms(product)
    if not platforms:
        return "No active channels specified. Use a balanced mix of practical text-first formats."

    notes: list[str] = [
        "Use the full set of active channels when choosing topics and formats.",
        "Do not rotate channels mechanically from item to item.",
        "Choose content ideas that stay strong as one core idea but can be adapted across the active channels.",
        "When a channel implies visuals or video, it is valid to propose carousel, reel, short video, or visual explainer formats.",
    ]

    if "telegram" in platforms:
        notes.append("Keep a strong share of concise, practical, hook-driven topics suitable for Telegram posts.")
    if "instagram" in platforms:
        notes.append("Include topics that can naturally become carousels, reels, caption-led posts, or visual explainers.")
    if "youtube" in platforms:
        notes.append("Include topics with strong video angles, walkthroughs, demos, or talking-head explanations.")
    if "blog" in platforms:
        notes.append("Include some topics that justify longer structured articles or case studies.")

    return "\n".join(f"- {note}" for note in notes)


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
    platforms = _get_active_channel_platforms(product)
    has_instagram = "instagram" in platforms
    has_youtube = "youtube" in platforms
    has_blog = "blog" in platforms

    templates = [
        {
            "title": f"How {focus} removes manual busywork",
            "angle": f"Show in plain language how {focus} reduces routine and chaos for {audience}.",
            "article_type": "educational",
        },
        {
            "title": f"5 real situations where {focus} already saves time",
            "angle": "Use concrete scenarios with immediate practical value and no technical overload.",
            "article_type": "listicle",
        },
        {
            "title": f"Why people delay using {focus} even when they know it could help",
            "angle": "Break down fear, delay, and perceived complexity that stop people from taking the first step.",
            "article_type": "educational",
        },
        {
            "title": f"How to tell whether {focus} is actually useful for your work",
            "angle": "Give simple criteria so a non-technical person can recognize genuine value.",
            "article_type": "checklist",
        },
        {
            "title": f"What is hype around {focus}, and what really works",
            "angle": "Compare empty promises with real workable scenarios.",
            "article_type": "comparison",
        },
        {
            "title": f"How to start using {focus} without getting lost in tools",
            "angle": "Create a low-friction entry path for non-technical readers through simple next steps.",
            "article_type": "guide",
        },
        {
            "title": f"How {focus} helps experts, practitioners, and small business owners",
            "angle": "Ground the idea in everyday work of specialists and small teams.",
            "article_type": "educational",
        },
        {
            "title": f"Which tasks should you give to {focus} first",
            "angle": "Highlight tasks with fast payoff and clear visible results.",
            "article_type": "checklist",
        },
    ]

    items: list[dict[str, Any]] = []
    for index in range(num_items):
        template = templates[index % len(templates)]
        article_type = template["article_type"]
        asset_brief = ""

        if has_youtube and index % 5 == 0:
            article_type = "reel"
            asset_brief = "Short vertical video with one example and one clear takeaway."
        elif has_instagram and index % 4 == 0:
            article_type = "carousel"
            asset_brief = "Carousel with 5-7 slides and one practical point per slide."
        elif has_blog and index % 6 == 0:
            article_type = "article"

        items.append(
            {
                "title": template["title"],
                "angle": template["angle"],
                "target_keywords": keywords,
                "article_type": article_type,
                "cta_type": "soft",
                "channel_targets": platforms,
                "asset_brief": asset_brief,
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
    active_channels = _get_active_channel_platforms(product)
    channel_strategy_notes = _build_channel_strategy_notes(product)

    system_prompt = f"""
You are a senior content strategist for a personal content autopilot.
Your job is to generate a list of {num_items} structured content plan items for a given month and theme.
Focus on creating high-signal, practical, and engaging topics that align with the brand, product, and active channel set.
Do not return generic or filler ideas. Make sure topics naturally progress throughout the month.

Return valid JSON with this exact shape:
{{
  "items": [
    {{
      "title": "string",
      "angle": "string",
      "target_keywords": ["string", "string"],
      "article_type": "string (e.g. educational, checklist, comparison, carousel, reel, article)",
      "cta_type": "string (e.g. soft, hard, none)",
      "channel_targets": ["telegram", "instagram"],
      "asset_brief": "string"
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

Active channels:
{_join_lines(active_channels)}

Channel strategy notes:
{channel_strategy_notes}

Plan month: {plan.month}
Plan theme: {theme_override or plan.theme or "General"}

Please generate {num_items} distinct content plan items that fit this theme and reflect the current channel set.
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
        .options(selectinload(ContentPlan.product).selectinload(Product.channels))
        .options(selectinload(ContentPlan.items))
    )
    plan = await session.scalar(plan_statement)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content plan not found")

    brand_profile = await session.scalar(select(BrandProfile).limit(1))
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
    new_items: list[ContentPlanItem] = []

    for i, data in enumerate(items_data):
        if not isinstance(data, dict):
            continue

        raw_keywords = data.get("target_keywords", [])
        target_keywords = raw_keywords if isinstance(raw_keywords, list) else []
        raw_targets = data.get("channel_targets", [])
        channel_targets = raw_targets if isinstance(raw_targets, list) else []

        item = ContentPlanItem(
            plan_id=plan.id,
            order=starting_order + i + 1,
            title=str(data.get("title") or f"Generated Item {i + 1}"),
            angle=str(data.get("angle") or ""),
            target_keywords=[str(keyword) for keyword in target_keywords if keyword],
            article_type=str(data.get("article_type") or "educational"),
            cta_type=str(data.get("cta_type") or "soft"),
            status="planned",
            research_data={
                "channel_targets": [str(target).strip().lower() for target in channel_targets if str(target).strip()],
                "asset_brief": str(data.get("asset_brief") or ""),
            },
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


async def generate_rewrite_items_from_ingested(
    session: AsyncSession,
    plan_id: uuid.UUID,
    ingested_content_ids: list[uuid.UUID],
) -> list[ContentPlanItem]:
    from app.models.monitoring import IngestedContent

    plan_statement = (
        select(ContentPlan)
        .where(ContentPlan.id == plan_id)
        .options(selectinload(ContentPlan.product).selectinload(Product.content_settings))
        .options(selectinload(ContentPlan.product).selectinload(Product.channels))
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
    channel_targets = _get_active_channel_platforms(plan.product)

    new_items: list[ContentPlanItem] = []

    for i, ingested in enumerate(ingested_items):
        angle = (
            f"Rewrite and adapt this viral {ingested.platform} content for {brand_name}: "
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
            research_data={
                "ingested_content_id": str(ingested.id),
                "raw": ingested.raw_data,
                "channel_targets": channel_targets,
            },
        )
        session.add(item)
        new_items.append(item)
        ingested.is_processed = True

    await session.commit()
    for item in new_items:
        await session.refresh(item)

    return new_items
