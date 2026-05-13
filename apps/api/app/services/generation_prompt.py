from __future__ import annotations

from datetime import datetime

from app.core.config import settings
from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product
from app.schemas.content_plan import PLAN_DIRECTION_KEYS

BASE_STRATEGY_RULES = """
Core product strategy:
- This content is for entrepreneurs, experts, marketers and small business owners in Russia/CIS who heard about AI but do not clearly understand how it applies to their business.
- The job of the post is to translate AI into recognizable business situations, pains, manual processes and practical opportunities.
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
- STRICTLY FORBIDDEN: Using outdated years (like 2025) as if they were current or future. We are in May 2026.
- AVOID: AI-cliches and over-used openings like "Imagine:", "In today's world:", "It's no secret that:", "We live in an era:", "Welcome to the future:".
- AVOID: Over-dramatizing business situations. Keep the tone grounded, professional, and practical.
""".strip()

POST_CONSTRUCTION_RULES = """
How to construct the post (Expert Narrative Architecture):
1. THE SHARP HOOK: Start with a non-obvious observation, a counter-intuitive fact, or a "brutal truth" about the current business process. No "In today's world" or "Imagine".
2. THE CONFLICT/DEPTH: Describe the invisible cost of the current manual process. Show the friction, the energy loss, and the systemic failure, not just "time loss".
3. THE MECHANISM (THE "HOW"): Explain exactly how the AI/automation works under the hood. Do not just say "it automates". Say "The agent parses the incoming intent, checks the client's history in the CRM, and generates a personalized offer based on previous purchase velocity."
4. THE CONCRETE CASE: Provide a detailed breakdown of a specific implementation. Include the "Before" (manual chaos) and "After" (automated system). Use specific numbers, roles, and process steps.
5. THE STRATEGIC INSIGHT: End with a conclusion that shifts the reader's perspective. Why is this a competitive advantage? What is the long-term impact on the business model?
6. FACT-DENSITY: Every sentence must contain a new fact, a specific action, or a logical step. Delete any sentence that serves as a generic transition.
7. TARGET LENGTH: Aim for 1500-2500 characters. Use the space to provide deep value, detailed examples, and thorough explanations. A post must be a "finished piece of information" - a holistic fact.
8. FORMATTING: Plain text only. Do NOT use markdown syntax: no **, no *, no __, no #, no >, no backticks. Use only paragraph breaks and numbered or dash lists where needed. Bold and italic will not render in the final channel.
""".strip()


def _join_lines(values: list[str]) -> str:
    if not values:
        return "not specified"
    return "\n".join(f"- {value}" for value in values)


def _build_channel_instruction(channels: list[str], *, include_illustration: bool = False, is_longread_capable: bool = False) -> str:
    normalized_channels = [channel.lower() for channel in channels]

    if "telegram" in normalized_channels:
        if is_longread_capable:
            return (
                "Primary format: Telegram longread.\n"
                "- draft_markdown must be a ready-to-post Telegram text.\n"
                "- You have a high character limit (up to 4000). Use it to provide deep value, detailed examples and thorough explanations.\n"
                "- Even for long posts, use short paragraphs, strong opening, and mobile-friendly formatting.\n"
                "- Do not use bulky section headers or article-style titles. Keep it a native Telegram post, just a deep and long one.\n"
                "- Avoid em dashes and en dashes. Prefer commas, periods, colons or a short hyphen when really needed.\n"
                "- Keep the result calm, practical, human and credible.\n"
                "- If an illustration is included, it will be sent together with the post."
            )
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
            "- Aim for 1200 to 2200 characters to ensure depth and holistic facts.\n"
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


def _build_cta_instruction(article_type: str | None, content_direction: str | None) -> str:
    is_practical = (article_type or "").strip().lower() in ("practical", "checklist")
    is_practical_direction = (content_direction or "").strip().lower() == "practical"
    if is_practical and is_practical_direction:
        return (
            "CTA rule: This is a practical business automation post. "
            "You MAY end with a single soft CTA if it fits naturally — point to @BusinessAdviserNew_bot "
            "where readers can quickly understand what to automate in their business. "
            "Only add the CTA if it flows naturally from the post content. "
            "Do not add a CTA if the post is about a general skill, mindset, or non-business topic."
        )
    return (
        "CTA rule: Do NOT add a CTA to this post. "
        "End on the content itself — the takeaway, insight, or practical conclusion. "
        "No call to action, no bot links, no 'if you want to know more' phrases."
    )


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
    
    is_longread_capable = bool(settings.telegram_api_id and settings.telegram_api_hash)
    channel_instruction = _build_channel_instruction(
        selected_channels, 
        include_illustration=include_illustration,
        is_longread_capable=is_longread_capable
    )
    direction_instruction = _build_direction_instruction(content_direction)
    cta_instruction = _build_cta_instruction(item.article_type, content_direction)

    system_prompt = f"""
You are a senior content strategist and writer for a personal content autopilot.
Today is {datetime.now().strftime('%Y-%m-%d')}.

Your job is to produce a high-quality first draft package for one content plan item.
IMPORTANT: All content must be strictly up-to-date. Ensure titles and topics are relevant for {datetime.now().year} and onwards. NEVER mention 2025 or other past years as if they were the current or upcoming year.
The output must be practical, specific, human-sounding, and useful.
Avoid generic AI filler, vague motivation, repetitive advice, bloated article structure and obvious AI phrasing patterns.
{BASE_STRATEGY_RULES}
{BASE_ANTI_RULES}
{POST_CONSTRUCTION_RULES}

{channel_instruction}
{direction_instruction}
{cta_instruction}

Visual Concept Guidelines (for asset_brief):
- Avoid generic stock-photo descriptions.
- Use visual metaphors that reflect the post's core message.
- MANDATORY: Include a "human factor" or something "alive" in the scene (a person, hands, a visible expert, a founder, a student, etc.). 
- Describe composition, lighting (e.g., "warm morning light"), and mood.
- Style should be editorial, clean, and modern.
- DO NOT use text in the image.

Return valid JSON with this shape:
{{
  "draft_title": "string",
  "draft_markdown": "string",
  "summary": "string",
  "hook": "string",
  "cta": "string",
  "asset_brief": "string",
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

Full product context (deep strategy — treat this as the primary source of intent):
{product.full_description or "not specified"}

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
- Make repurposing outputs materially useful, not placeholders.
- Avoid long dashes in every field of the response.
- If manual brief is present, treat it as the main source of intent and build the post around it.
- Respect the requested content direction and do not force everything into practical business advice.
- If the direction is practical, include concrete examples and specific scenarios, not just general recommendations.
- Make the reader recognize themselves in the situation whenever possible.
- Show what is actually broken: time loss, lead loss, routine, chaos, weak handoffs, poor follow-up or missing system.
- If you mention AI, bots or automation, connect them to a concrete business process, not to abstract tool enthusiasm.
- Do not suggest that a random prompt alone solves the business problem if the real issue is process, data, CRM, logic or follow-up.
- Do not start the post from the tool itself. Start from the recognizable business situation and use the tool, release, case or innovation only as the practical angle.
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
