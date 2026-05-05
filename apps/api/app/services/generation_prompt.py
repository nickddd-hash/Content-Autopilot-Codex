from __future__ import annotations

from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product
from app.schemas.content_plan import PLAN_DIRECTION_KEYS

BASE_STRATEGY_RULES = """
Core product strategy:
- This content is for entrepreneurs, experts, marketers and small business owners in Russia/CIS who heard about AI but do not clearly understand how it applies to their business.
- The job of the post is to translate AI into recognizable business situations, pains, manual processes and practical opportunities.
- The content should move the reader from abstract interest toward a concrete next step: a free AI business audit/helper that asks 7 short questions and returns a diagnosis, 3 automation priorities, a quick win, suitable tools and an approximate ROI.
- The writer voice should feel like a practical translator between AI and business, not like a hype commentator or generic AI educator.
""".strip()

BASE_ANTI_RULES = """
What must not appear by default:
- DIY framing like "build it yourself tonight"
- no-code/constructor evangelism as the main answer
- fake first-person stories or invented personal experience
- broad AI hype with no recognizable business situation
- abstract advice with no concrete process, task or consequence
- technical overload, stack talk and jargon for non-technical readers
- aggressive selling, empty motivation or consultant cliches
- western tools as the everyday default for Russia/CIS unless there is a clear reason
""".strip()

POST_CONSTRUCTION_RULES = """
How to construct the post:
- Start from a recognizable business pain or situation, not from a tool, release or hype topic.
- Identify where the problem shows up in the business process.
- Use the tool, AI release, case or innovation only as a fresh angle on that business pain.
- Repeated pains are allowed, but the post must add new value through a new solution, new audience angle, new process angle, new limitation, new case or new implementation model.
""".strip()


def _join_lines(values: list[str]) -> str:
    if not values:
        return "not specified"
    return "\n".join(f"- {value}" for value in values)


def _build_channel_instruction(channels: list[str], *, include_illustration: bool = False) -> str:
    normalized_channels = [channel.lower() for channel in channels]

    if "telegram" in normalized_channels:
        if include_illustration:
            return (
                "Primary format: Telegram post with illustration.\n"
                "- draft_markdown must be a ready-to-post Telegram text, not an article.\n"
                "- Aim for roughly 500 to 850 characters.\n"
                "- The post must fit into one Telegram publication together with an illustration caption.\n"
                "- Use short paragraphs, strong opening, concrete examples and one clear takeaway.\n"
                "- Do not use long article headings, subheadings or bulky section structure.\n"
                "- Avoid em dashes and en dashes. Prefer commas, periods, colons or a short hyphen when really needed.\n"
                "- Keep the result calm, practical, human and easy to read on mobile.\n"
                "- The post should feel publishable with minimal editing."
            )
        return (
            "Primary format: Telegram post.\n"
            "- draft_markdown must be a ready-to-post Telegram text, not an article.\n"
            "- Aim for roughly 600 to 900 characters.\n"
            "- Keep the post short enough to fit into one Telegram publication together with an illustration.\n"
            "- Use short paragraphs, strong opening, concrete examples and one clear takeaway.\n"
            "- Do not use long article headings, subheadings or bulky section structure.\n"
            "- Avoid em dashes and en dashes. Prefer commas, periods, colons or a short hyphen when really needed.\n"
            "- Keep the result calm, practical, human and easy to read on mobile.\n"
            "- The post should feel publishable with minimal editing."
        )

    return (
        "Primary format: concise educational post.\n"
        "- draft_markdown should still be compact and practical.\n"
        "- Avoid long-form article structure unless the context clearly demands it.\n"
        "- Avoid em dashes and en dashes in the final wording."
    )


def _build_direction_instruction(direction: str | None) -> str:
    normalized = (direction or "").strip().lower()
    if normalized not in PLAN_DIRECTION_KEYS:
        return (
            "Content direction: general.\n"
            "- Keep the post aligned with the brief, without forcing it into product promotion.\n"
        )

    direction_map = {
        "practical": (
            "Content direction: practical.\n"
            "- Focus on real use cases, applied value, simple steps and concrete outcomes.\n"
            "- Give specific examples, concrete scenarios, typical tasks, before/after effects and clear practical details.\n"
            "- Do not stay at the level of abstract advice. Show what exactly happens, for whom, in which situation and with what result.\n"
            "- If you mention automation or bots, describe concrete business or work situations rather than generic tool talk.\n"
        ),
        "educational": (
            "Content direction: educational.\n"
            "- Explain clearly, simply and calmly.\n"
            "- Do not force the post into business use cases if the brief is broader.\n"
            "- General educational framing is allowed if the brief is about understanding AI, not using it at work.\n"
        ),
        "news": (
            "Content direction: news.\n"
            "- Frame the post as an understandable reaction to an AI development or update.\n"
            "- Keep it clear, contextual and human, not like a newsroom article.\n"
        ),
        "opinion": (
            "Content direction: opinion.\n"
            "- Write as a thoughtful personal viewpoint.\n"
            "- Allow a broader, reflective or philosophical angle if the brief suggests it.\n"
            "- Do not drag the post back into product advice unless the brief asks for it.\n"
            "- It is valid to focus on human, cultural or life-related implications of AI.\n"
        ),
        "critical": (
            "Content direction: critical.\n"
            "- Use a skeptical, grounded angle.\n"
            "- Highlight limits, overpromises or blind spots without sounding cynical.\n"
        ),
    }
    return direction_map[normalized]


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
    manual_brief = ""
    content_direction = ""
    include_illustration = False
    available_channels = [str(channel).strip() for channel in product.primary_channels if str(channel).strip()]
    selected_channels = list(available_channels)
    if isinstance(item.research_data, dict):
        raw_manual_brief = item.research_data.get("manual_brief")
        if isinstance(raw_manual_brief, str):
            manual_brief = raw_manual_brief.strip()
        raw_direction = item.research_data.get("content_direction")
        if isinstance(raw_direction, str):
            content_direction = raw_direction.strip().lower()
        raw_channels = item.research_data.get("channel_targets")
        if isinstance(raw_channels, list):
            requested_channels = [str(channel).strip() for channel in raw_channels if str(channel).strip()]
            if available_channels:
                selected_channels = [channel for channel in requested_channels if channel in available_channels]
            else:
                selected_channels = requested_channels
        raw_include_illustration = item.research_data.get("include_illustration")
        if isinstance(raw_include_illustration, bool):
            include_illustration = raw_include_illustration
    if not selected_channels:
        selected_channels = list(available_channels)
    channel_instruction = _build_channel_instruction(selected_channels, include_illustration=include_illustration)
    direction_instruction = _build_direction_instruction(content_direction)

    system_prompt = f"""
You are a senior content strategist and writer for a personal content autopilot.

Your job is to produce a high-quality first draft package for one content plan item.
The output must be practical, specific, human-sounding, and useful.
Avoid generic AI filler, vague motivation, repetitive advice, bloated article structure and obvious AI phrasing patterns.
{BASE_STRATEGY_RULES}
{BASE_ANTI_RULES}
{POST_CONSTRUCTION_RULES}

{channel_instruction}
{direction_instruction}

Return valid JSON with this shape:
{{
  "draft_title": "string",
  "draft_markdown": "string",
  "summary": "string",
  "hook": "string",
  "cta": "string",
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

Selected channels for this item:
{_join_lines(selected_channels)}

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

Manual author brief:
{manual_brief or "not specified"}

Requested content direction:
{content_direction or "not specified"}

Requirements:
- Produce a practical, useful, high-signal first draft.
- The writing should feel like a real expert draft, not synthetic filler.
- Keep the voice calm, clear, intelligent, credible and easy to read.
- Prefer one compact Telegram-ready post over a long article.
- Use a strong hook and a soft CTA unless the brief clearly needs a different CTA.
- Make repurposing outputs materially useful, not placeholders.
- Avoid long dashes in every field of the response.
- If manual brief is present, treat it as the main source of intent and build the post around it.
- Respect the requested content direction and do not force everything into practical business advice.
- If the direction is practical, include concrete examples and specific scenarios, not just general recommendations.
- Make the reader recognize themselves in the situation whenever possible.
- Show what is actually broken: time loss, lead loss, routine, chaos, weak handoffs, poor follow-up or missing system.
- If you mention AI, bots or automation, connect them to a concrete business process, not to abstract tool enthusiasm.
- Prefer soft CTAs that lead to diagnosis, audit, consultation or implementation help, not to self-assembly.
- Do not suggest that a random prompt alone solves the business problem if the real issue is process, data, CRM, logic or follow-up.
- Do not start the post from the tool itself. Start from the recognizable business situation and use the tool, release, case or innovation only as the practical angle.
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
