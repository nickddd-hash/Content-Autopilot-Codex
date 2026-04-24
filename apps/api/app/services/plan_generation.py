from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product
from app.schemas.content_plan import PLAN_DIRECTION_KEYS
from app.services.llm_client import LLMClientError, generate_json

DEFAULT_CONTENT_MIX: dict[str, int] = {
    "practical": 40,
    "educational": 25,
    "news": 15,
    "opinion": 10,
    "critical": 10,
}

DIRECTION_LABELS: dict[str, str] = {
    "practical": "practical",
    "educational": "educational",
    "news": "news",
    "opinion": "opinion",
    "critical": "critical",
}

DIRECTION_HINTS: dict[str, str] = {
    "practical": "practical use cases, workflows, savings of time, reduction of chaos, concrete scenarios",
    "educational": "simple explanation, AI basics, terminology, first principles, public education without jargon",
    "news": "important AI updates, launches, releases, public developments explained in plain language",
    "opinion": "author perspective, interpretation, thoughtful viewpoint, what matters and what does not",
    "critical": "skeptical angle, hype check, limitations, risks, overpromises, what is overrated",
}


def _join_lines(values: list[str]) -> str:
    if not values:
        return "not specified"
    return "\n".join(f"- {value}" for value in values)


def _normalize_content_mix(raw_settings: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(raw_settings, dict):
        return dict(DEFAULT_CONTENT_MIX)

    raw_mix = raw_settings.get("content_mix", raw_settings)
    if not isinstance(raw_mix, dict):
        return dict(DEFAULT_CONTENT_MIX)

    mix: dict[str, int] = {}
    for key in PLAN_DIRECTION_KEYS:
        raw_value = raw_mix.get(key, DEFAULT_CONTENT_MIX[key])
        try:
            mix[key] = max(0, min(100, int(raw_value)))
        except (TypeError, ValueError):
            mix[key] = DEFAULT_CONTENT_MIX[key]

    if sum(mix.values()) <= 0:
        return dict(DEFAULT_CONTENT_MIX)

    return mix


def _allocate_direction_sequence(num_items: int, mix: dict[str, int]) -> list[str]:
    active = {key: value for key, value in mix.items() if value > 0}
    if not active:
        active = dict(DEFAULT_CONTENT_MIX)

    total_weight = sum(active.values())
    raw_counts = {key: (num_items * value) / total_weight for key, value in active.items()}
    counts = {key: int(raw_counts[key]) for key in active}
    remainder = num_items - sum(counts.values())

    fractions = sorted(
        active,
        key=lambda key: (raw_counts[key] - counts[key], active[key]),
        reverse=True,
    )
    for key in fractions[:remainder]:
        counts[key] += 1

    sequence: list[str] = []
    remaining = counts.copy()
    while len(sequence) < num_items:
        ordered = sorted(
            [key for key, value in remaining.items() if value > 0],
            key=lambda key: (remaining[key], active[key]),
            reverse=True,
        )
        if not ordered:
            break
        for key in ordered:
            if remaining[key] <= 0:
                continue
            sequence.append(key)
            remaining[key] -= 1
            if len(sequence) == num_items:
                break

    return sequence


def _build_mix_summary(mix: dict[str, int], num_items: int) -> str:
    lines = []
    for direction in _allocate_direction_sequence(num_items, mix):
        lines.append(direction)
    counts: dict[str, int] = {key: lines.count(key) for key in PLAN_DIRECTION_KEYS if key in lines}
    if not counts:
        counts = {key: 0 for key in PLAN_DIRECTION_KEYS}
    return "\n".join(
        f"- {key}: {mix[key]}% target, around {counts.get(key, 0)} items"
        for key in PLAN_DIRECTION_KEYS
        if mix.get(key, 0) > 0
    )


def _build_directional_fallback_item(
    direction: str,
    focus: str,
    audience: str,
    index: int,
) -> dict[str, Any]:
    practical = [
        (
            f"Где {focus} реально экономит время уже на первой неделе",
            f"Показать через 3 простых сценария, как {focus} снижает рутину для аудитории: {audience}.",
            "checklist",
        ),
        (
            f"С чего начать {focus}, если в работе много хаоса",
            "Дать спокойный и понятный вход без перегруза инструментами и техничностью.",
            "guide",
        ),
    ]
    educational = [
        (
            f"Что такое {focus} простыми словами и без перегруза",
            "Объяснить тему человеческим языком для людей, которые знакомы с AI только поверхностно.",
            "educational",
        ),
        (
            f"Что люди чаще всего неправильно понимают про {focus}",
            "Разобрать базовые заблуждения и снять тревогу вокруг AI.",
            "educational",
        ),
    ]
    news = [
        (
            f"Что нового происходит вокруг {focus} и почему это вообще важно",
            "Взять новостной или обзорный угол и объяснить его простым языком без шума.",
            "news",
        ),
        (
            f"Какие AI-новости действительно стоит отслеживать, а какие нет",
            "Показать читателю, как отличать важные сигналы от хайпа.",
            "news",
        ),
    ]
    opinion = [
        (
            f"Мой взгляд на {focus}: что здесь действительно важно",
            "Дать зрелую позицию без пафоса и техно-восторга.",
            "opinion",
        ),
        (
            f"Почему разговор о {focus} часто уходит не туда",
            "Показать авторское мнение и переупаковать тему в ясную рамку.",
            "opinion",
        ),
    ]
    critical = [
        (
            f"Где вокруг {focus} слишком много хайпа и слишком мало пользы",
            "Критически разобрать завышенные ожидания и вернуть разговор в реальность.",
            "critical",
        ),
        (
            f"Почему не всё в {focus} стоит внедрять или повторять",
            "Показать ограничения, риски и ложные ожидания без алармизма.",
            "critical",
        ),
    ]

    templates_by_direction = {
        "practical": practical,
        "educational": educational,
        "news": news,
        "opinion": opinion,
        "critical": critical,
    }
    templates = templates_by_direction.get(direction, educational)
    title, angle, article_type = templates[index % len(templates)]

    return {
        "title": title,
        "angle": angle,
        "target_keywords": [focus, direction, "AI"],
        "article_type": article_type,
        "cta_type": "soft",
        "content_direction": direction,
    }


def _build_fallback_plan_items(
    product: Product,
    plan: ContentPlan,
    num_items: int,
    theme_override: str | None = None,
) -> list[dict[str, Any]]:
    focus = theme_override or plan.theme or product.value_proposition or product.short_description or product.name
    audience = product.target_audience or "non-technical entrepreneurs and practitioners"
    mix = _normalize_content_mix(getattr(plan, "settings_json", None))
    directions = _allocate_direction_sequence(num_items, mix)

    items: list[dict[str, Any]] = []
    for index, direction in enumerate(directions):
        items.append(_build_directional_fallback_item(direction, focus, audience, index))
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
    mix = _normalize_content_mix(getattr(plan, "settings_json", None))
    direction_targets = _build_mix_summary(mix, num_items)
    direction_hints = "\n".join(f"- {key}: {DIRECTION_HINTS[key]}" for key in PLAN_DIRECTION_KEYS if mix.get(key, 0) > 0)

    system_prompt = f"""
You are a senior content strategist for a personal content autopilot.
Your job is to generate a list of {num_items} structured content plan items for a given month and theme.
Focus on creating high-signal, practical, understandable, varied topics that align with the brand and product.
Do not collapse every topic into business automation. Keep a healthy mix of practical, educational, news, opinion and critical topics when requested.

Return valid JSON with this exact shape:
{{
  "items": [
    {{
      "title": "string",
      "angle": "string",
      "target_keywords": ["string", "string"],
      "article_type": "string (e.g. educational, checklist, comparison, news, opinion, critical)",
      "cta_type": "string (e.g. soft, hard, none)",
      "content_direction": "string (one of practical, educational, news, opinion, critical)"
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
Requested content mix:
{direction_targets}

Direction guidance:
{direction_hints}

Requirements:
- Generate {num_items} distinct items.
- Follow the requested mix approximately.
- At least some items should be broad educational or public-interest AI topics when educational/news/opinion/critical directions are enabled.
- Explain AI in simple human language.
- Avoid making every item about business efficiency.
- Keep titles specific and easy to understand.
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

    starting_order = max([item.order for item in plan.items], default=-1)
    new_items: list[ContentPlanItem] = []

    for index, data in enumerate(items_data):
        if not isinstance(data, dict):
            continue

        raw_keywords = data.get("target_keywords", [])
        target_keywords = raw_keywords if isinstance(raw_keywords, list) else []
        direction = str(data.get("content_direction") or "educational").lower().strip()
        if direction not in PLAN_DIRECTION_KEYS:
            direction = "educational"

        item = ContentPlanItem(
            plan_id=plan.id,
            order=starting_order + index + 1,
            title=str(data.get("title") or f"Generated Item {index + 1}"),
            angle=str(data.get("angle") or ""),
            target_keywords=[str(keyword) for keyword in target_keywords if keyword],
            article_type=str(data.get("article_type") or direction),
            cta_type=str(data.get("cta_type") or "soft"),
            status="planned",
            research_data={
                "content_direction": direction,
                "channel_targets": list(plan.product.primary_channels or []),
                "include_illustration": True,
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

    starting_order = max((item.order for item in plan.items), default=-1)
    brand_profile = await session.scalar(select(BrandProfile).limit(1))
    brand_name = brand_profile.brand_name if brand_profile and brand_profile.brand_name else plan.product.name

    new_items: list[ContentPlanItem] = []

    for index, ingested in enumerate(ingested_items):
        angle = (
            f"Rewrite & adapt this viral {ingested.platform} content for {brand_name}: "
            f"\"{(ingested.text_content or '')[:300]}\" "
            f"(engagement score: {ingested.engagement_score:.0%})"
        )
        item = ContentPlanItem(
            plan_id=plan.id,
            order=starting_order + index + 1,
            title=f"[Rewrite] {ingested.platform.capitalize()} Viral Content #{index + 1}",
            angle=angle,
            target_keywords=[],
            article_type="rewrite",
            cta_type="soft",
            status="planned",
            research_data={"ingested_content_id": str(ingested.id), "raw": ingested.raw_data},
        )
        session.add(item)
        new_items.append(item)
        ingested.is_processed = True

    await session.commit()
    for item in new_items:
        await session.refresh(item)

    return new_items
