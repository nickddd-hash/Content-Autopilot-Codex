from __future__ import annotations

from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product


def _join_lines(values: list[str]) -> str:
    if not values:
        return "not specified"
    return "\n".join(f"- {value}" for value in values)


def _get_active_channel_descriptions(product: Product) -> list[str]:
    descriptions: list[str] = []

    for channel in getattr(product, "channels", []) or []:
        if not getattr(channel, "is_active", True):
            continue
        platform = (getattr(channel, "platform", "") or "unknown").strip().lower()
        name = (getattr(channel, "name", "") or "").strip()
        descriptions.append(f"{platform}: {name}" if name else platform)

    if descriptions:
        return descriptions

    return [channel for channel in (product.primary_channels or []) if channel]


def _build_channel_generation_rules(channel_descriptions: list[str]) -> str:
    channel_list = _join_lines(channel_descriptions)

    return f"""
Active channels:
{channel_list}

Channel rules:
- The main `draft_markdown` should be a canonical master version of the content idea.
- Also return `channel_adaptations` for each active channel you can identify.
- Keep the core idea the same across channels, but adapt packaging, rhythm, and formatting to the channel.
- Do not produce the exact same wording for every channel.
- If Telegram is present, include a concise Telegram-ready version with a strong hook and short paragraphs.
- If Instagram is present, include adaptations suitable for carousel/reel caption logic.
- If YouTube is present, include a video-oriented adaptation angle where relevant.
- If blog is present, include a more structured long-form adaptation where relevant.
- If some channels imply visuals or video, include `asset_brief` suggestions for them.
""".strip()


def build_generation_messages(
    product: Product,
    brand_profile: BrandProfile | None,
    plan: ContentPlan,
    item: ContentPlanItem,
) -> list[dict[str, str]]:
    brand_name = brand_profile.brand_name if brand_profile and brand_profile.brand_name else product.name
    brand_summary = (
        brand_profile.brand_summary
        if brand_profile and brand_profile.brand_summary
        else product.short_description or product.value_proposition or "No brand summary provided."
    )
    audience_notes = brand_profile.audience_notes if brand_profile else []
    core_messages = brand_profile.core_messages if brand_profile else []
    allowed_tone = brand_profile.allowed_tone if brand_profile else []
    disallowed_tone = brand_profile.disallowed_tone if brand_profile else []
    compliance_rules = brand_profile.compliance_rules if brand_profile else []
    cta_rules = brand_profile.cta_rules if brand_profile else []
    formatting_rules = brand_profile.formatting_rules if brand_profile else []
    anti_slop_rules = brand_profile.anti_slop_rules if brand_profile else []
    active_channels = _get_active_channel_descriptions(product)
    channel_rules = _build_channel_generation_rules(active_channels)

    system_prompt = f"""
You are a senior content strategist and writer for a personal content autopilot.

Your job is to produce a high-quality first draft package for one content plan item.
The output must be practical, specific, human-sounding, and useful.
Avoid generic AI filler, vague motivation, or repetitive advice.

Return valid JSON with this shape:
{{
  "draft_title": "string",
  "draft_markdown": "string",
  "summary": "string",
  "hook": "string",
  "cta": "string",
  "channel_adaptations": {{
    "telegram": {{
      "format": "telegram_post",
      "content_markdown": "string",
      "asset_brief": "string"
    }}
  }},
  "repurposing": {{
    "post": "string",
    "carousel": ["string", "string"],
    "reel_script": "string"
  }},
  "review_notes": ["string", "string"]
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

Strategic goals:
{_join_lines(product.strategic_goals)}

Primary channels:
{_join_lines(product.primary_channels)}

Active distribution channels:
{_join_lines(active_channels)}

Tone of voice:
{product.tone_of_voice or "not specified"}

Brand audience notes:
{_join_lines(audience_notes)}

Core messages:
{_join_lines(core_messages)}

Allowed tone:
{_join_lines(allowed_tone)}

Disallowed tone:
{_join_lines(disallowed_tone)}

Compliance rules:
{_join_lines(compliance_rules)}

CTA rules:
{_join_lines(cta_rules)}

Formatting rules:
{_join_lines(formatting_rules)}

Anti-slop rules:
{_join_lines(anti_slop_rules)}

Plan month: {plan.month}
Plan theme: {plan.theme}
Plan item title: {item.title}
Plan item angle: {item.angle or "not specified"}
Target keywords:
{_join_lines(item.target_keywords)}
Article type: {item.article_type}
CTA type: {item.cta_type}

Requirements:
- Produce a practical, useful, high-signal first draft.
- The master draft should feel like a real expert-writer draft, not synthetic filler.
- Keep the voice calm, clear, intelligent, and credible.
- Give a strong hook and a soft CTA.
- Make repurposing outputs materially useful, not placeholders.
- Adapt the output to the product's active channels.

{channel_rules}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
