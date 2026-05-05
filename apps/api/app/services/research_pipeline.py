from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.parse import quote_plus, urlparse
from xml.etree import ElementTree

import httpx
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentPlan, ContentPlanItem, PlanResearchLink, Product, ResearchCandidate, ResearchSource, TopicMemory
from app.services.llm_client import LLMClientError, generate_json

GOOGLE_NEWS_RSS_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru"
RESEARCH_WINDOW_DAYS = 21
MEMORY_WINDOW_DAYS = 120

PAIN_CLUSTERS: dict[str, tuple[str, ...]] = {
    "lost_leads": ("заяв", "lead", "лид", "конверс", "обращен", "продаж", "воронк"),
    "follow_up_gap": ("follow", "догрев", "напомин", "дожим", "касани", "ответ"),
    "crm_chaos": ("crm", "amo", "битрикс", "воронк", "карточ", "сделк"),
    "content_chaos": ("контент", "content", "блог", "telegram", "дезен", "пост"),
    "support_overload": ("поддерж", "support", "faq", "вопрос", "чат", "консульт"),
    "onboarding_friction": ("онборд", "onboarding", "адаптац", "приветств", "ввод"),
    "manual_routine": ("рутин", "manual", "ручн", "таблиц", "excel", "копир"),
    "scheduling_bottleneck": ("запис", "schedule", "календар", "слот", "бронир"),
}

BUSINESS_PROCESSES: dict[str, tuple[str, ...]] = {
    "leads": ("заяв", "lead", "лид", "обращен"),
    "follow_up": ("follow", "догрев", "напомин", "ответ"),
    "crm": ("crm", "amo", "битрикс", "сделк"),
    "content": ("контент", "content", "telegram", "dzen", "дзен", "блог"),
    "support": ("поддерж", "support", "чат", "вопрос"),
    "onboarding": ("онборд", "onboarding", "ввод"),
    "internal_ops": ("процесс", "операцион", "команд", "рутин", "таблиц", "excel"),
    "scheduling": ("запис", "schedule", "календар", "бронир"),
}

SOLUTION_TYPES: dict[str, tuple[str, ...]] = {
    "ai_assistant": ("assistant", "ассистент", "copilot", "ai-agent", "агент"),
    "telegram_bot": ("telegram", "бот", "bot"),
    "crm_automation": ("crm", "amo", "битрикс", "воронк"),
    "workflow_automation": ("automation", "автомат", "workflow", "интеграц"),
    "content_system": ("контент", "content", "редакц", "пост", "блог"),
    "analytics_layer": ("аналит", "отч", "метрик", "dashboard"),
}

IMPLEMENTATION_MODELS: dict[str, tuple[str, ...]] = {
    "mvp": ("mvp", "быстр", "cheap", "недел", "за день"),
    "bot_plus_crm": ("crm", "бот", "telegram"),
    "ai_plus_workflow": ("ai", "автомат", "workflow", "интеграц"),
    "manual_plus_ai": ("ручн", "semi", "partial", "copilot"),
    "full_system": ("система", "platform", "сквозн", "end-to-end"),
}

ANGLE_PATTERNS: dict[str, tuple[str, ...]] = {
    "case_breakdown": ("кейс", "case", "пример", "как сделали"),
    "comparison": ("сравн", "versus", "vs", "compare"),
    "critical_view": ("ошиб", "risk", "риск", "провал", "limit", "огранич"),
    "build_in_public": ("build", "собира", "внедря", "делаем"),
    "quick_win": ("быстро", "quick", "сразу", "на этой неделе"),
    "news_with_takeaway": ("нов", "release", "релиз", "launch", "обнов"),
}


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fit_label(value: str | None, *, limit: int = 100, fallback: str = "not_specified") -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return fallback
    return cleaned[:limit]


def _normalize_lookup_text(value: str) -> str:
    normalized = value.lower().replace("ё", "е")
    normalized = re.sub(r"[^a-zа-я0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _detect_by_keywords(text: str, mapping: dict[str, tuple[str, ...]], fallback: str) -> str:
    normalized = _normalize_lookup_text(text)
    scores: dict[str, int] = {}
    for key, keywords in mapping.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score > 0:
            scores[key] = score
    if not scores:
        return fallback
    return max(scores.items(), key=lambda item: item[1])[0]


def _guess_pain_cluster(text: str) -> str:
    return _detect_by_keywords(text, PAIN_CLUSTERS, "manual_routine")


def _guess_business_process(text: str) -> str:
    return _detect_by_keywords(text, BUSINESS_PROCESSES, "internal_ops")


def _guess_solution_type(text: str) -> str:
    return _detect_by_keywords(text, SOLUTION_TYPES, "workflow_automation")


def _guess_implementation_model(text: str) -> str:
    return _detect_by_keywords(text, IMPLEMENTATION_MODELS, "ai_plus_workflow")


def _guess_angle(text: str) -> str:
    return _detect_by_keywords(text, ANGLE_PATTERNS, "case_breakdown")


def _guess_signal_type(text: str) -> str:
    normalized = _normalize_lookup_text(text)
    if any(keyword in normalized for keyword in ("релиз", "release", "launch", "анонс", "обнов")):
        return "new_tool"
    if any(keyword in normalized for keyword in ("кейс", "case", "пример")):
        return "new_case"
    if any(keyword in normalized for keyword in ("ошиб", "risk", "limit", "огранич", "провал")):
        return "new_limitation"
    if any(keyword in normalized for keyword in ("trend", "тренд", "рынок")):
        return "new_trend"
    return "new_solution"


def _guess_audience_segment(text: str, product: Product) -> str:
    normalized = _normalize_lookup_text(text)
    if any(keyword in normalized for keyword in ("маркет", "агентств", "продюсер")):
        return "marketers"
    if any(keyword in normalized for keyword in ("эксперт", "консульт", "коуч", "практик")):
        return "experts"
    if any(keyword in normalized for keyword in ("салон", "клиник", "студи", "ресторан")):
        return "local_services"
    if any(keyword in normalized for keyword in ("школ", "курс", "образоват")):
        return "education_projects"
    if product.audience_segments:
        first_segment = str(product.audience_segments[0]).strip()
        if first_segment:
            return first_segment[:100]
    return "small_business"


def _extract_tools(text: str) -> list[str]:
    normalized = _clean_text(text)
    known_tools = [
        "ChatGPT",
        "Claude",
        "Gemini",
        "DeepSeek",
        "Telegram",
        "amoCRM",
        "Bitrix24",
        "Notion",
        "Airtable",
        "Google Sheets",
    ]
    return [tool for tool in known_tools if tool.lower() in normalized.lower()]


def _derive_keywords(text: str, max_items: int = 6) -> list[str]:
    normalized = _normalize_lookup_text(text)
    tokens = [token for token in normalized.split() if len(token) > 3]
    deduped: list[str] = []
    for token in tokens:
        if token not in deduped:
            deduped.append(token)
        if len(deduped) >= max_items:
            break
    return deduped


def _build_duplicate_group_key(
    pain_cluster: str,
    audience_segment: str,
    business_process: str,
    solution_type: str,
    angle: str,
) -> str:
    return "::".join([pain_cluster, audience_segment, business_process, solution_type, angle])


def _build_novelty_signature(
    *,
    pain_cluster: str,
    audience_segment: str,
    business_process: str,
    solution_type: str,
    implementation_model: str,
    angle: str,
) -> dict[str, str]:
    return {
        "pain_cluster": pain_cluster,
        "audience_segment": audience_segment,
        "business_process": business_process,
        "solution_type": solution_type,
        "implementation_model": implementation_model,
        "angle": angle,
    }


def _parse_published_at(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    try:
        parsed = parsedate_to_datetime(raw_value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


async def _fetch_google_news_rss(query: str) -> list[dict[str, Any]]:
    url = GOOGLE_NEWS_RSS_TEMPLATE.format(query=quote_plus(query))
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    root = ElementTree.fromstring(response.text)
    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title = _clean_text(item.findtext("title"))
        link = _clean_text(item.findtext("link"))
        description = _clean_text(item.findtext("description"))
        pub_date = _clean_text(item.findtext("pubDate"))
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "url": link,
                "snippet": description,
                "published_at": _parse_published_at(pub_date),
                "source_type": "google_news_rss",
                "domain": urlparse(link).netloc.lower() or None,
                "language": "ru",
                "raw_payload_json": {"query": query},
            }
        )
    return items


def _build_research_queries(product: Product, theme_override: str | None = None) -> list[str]:
    queries: list[str] = []
    if theme_override and theme_override.strip():
        queries.append(f"{theme_override.strip()} AI автоматизация бизнес")

    base_terms = [product.name]
    base_terms.extend(str(value).strip() for value in product.content_pillars[:3] if str(value).strip())
    base_terms.extend(str(value).strip() for value in product.pain_points[:3] if str(value).strip())

    seen: set[str] = set()
    for term in base_terms:
        if not term:
            continue
        compact = term.strip()
        if compact in seen:
            continue
        seen.add(compact)
        queries.append(f"{compact} AI кейс автоматизация")
        queries.append(f"{compact} Telegram CRM автоматизация")

    queries.extend(
        [
            "малый бизнес AI автоматизация кейс",
            "Telegram бот CRM заявки автоматизация",
            "AI ассистент малый бизнес кейс",
            "AI автоматизация контента малый бизнес",
            "AI внедрение бизнес ошибки кейс",
        ]
    )

    deduped: list[str] = []
    seen_queries: set[str] = set()
    for query in queries:
        normalized = query.lower().strip()
        if normalized in seen_queries:
            continue
        seen_queries.add(normalized)
        deduped.append(query)
        if len(deduped) >= 10:
            break
    return deduped


async def _upsert_research_source(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    payload: dict[str, Any],
) -> ResearchSource:
    statement: Select[tuple[ResearchSource]] = select(ResearchSource).where(
        ResearchSource.product_id == product_id,
        ResearchSource.source_type == str(payload.get("source_type") or "web"),
        ResearchSource.url == str(payload.get("url") or ""),
    )
    existing = await session.scalar(statement)
    if existing is not None:
        candidate_exists = await session.scalar(
            select(ResearchCandidate.id)
            .where(ResearchCandidate.source_id == existing.id)
            .limit(1)
        )
        existing.title = str(payload.get("title") or existing.title)
        existing.domain = payload.get("domain") or existing.domain
        existing.published_at = payload.get("published_at") or existing.published_at
        existing.raw_snippet = str(payload.get("snippet") or existing.raw_snippet or "")
        existing.raw_payload_json = {
            **(existing.raw_payload_json if isinstance(existing.raw_payload_json, dict) else {}),
            **(payload.get("raw_payload_json") or {}),
        }
        existing.language = payload.get("language") or existing.language
        existing.status = "processed" if candidate_exists else "new"
        return existing

    source = ResearchSource(
        product_id=product_id,
        source_type=str(payload.get("source_type") or "web"),
        title=str(payload.get("title") or "").strip()[:500],
        url=str(payload.get("url") or "").strip()[:1000],
        domain=payload.get("domain"),
        published_at=payload.get("published_at"),
        raw_snippet=str(payload.get("snippet") or "").strip() or None,
        raw_payload_json=payload.get("raw_payload_json") or {},
        language=payload.get("language"),
        status="new",
    )
    session.add(source)
    await session.flush()
    return source


def _fallback_candidate_from_source(product: Product, source: ResearchSource) -> dict[str, Any]:
    combined_text = " ".join(filter(None, [source.title, source.raw_snippet or ""]))
    pain_cluster = _guess_pain_cluster(combined_text)
    audience_segment = _guess_audience_segment(combined_text, product)
    business_process = _guess_business_process(combined_text)
    solution_type = _guess_solution_type(combined_text)
    implementation_model = _guess_implementation_model(combined_text)
    angle = _guess_angle(combined_text)
    signal_type = _guess_signal_type(combined_text)
    tools = _extract_tools(combined_text)
    keywords = _derive_keywords(combined_text)
    strategy_fit = 70 if pain_cluster in {"lost_leads", "crm_chaos", "manual_routine", "content_chaos"} else 58
    relevance = 72 if business_process in {"leads", "follow_up", "crm", "content"} else 60
    novelty = 62 if signal_type in {"new_tool", "new_case", "new_limitation"} else 55
    priority = int(round((strategy_fit * 0.4) + (relevance * 0.35) + (novelty * 0.25)))

    return {
        "source_id": str(source.id),
        "title": source.title,
        "summary": source.raw_snippet or source.title,
        "pain_cluster": pain_cluster,
        "audience_segment": audience_segment,
        "business_process": business_process,
        "solution_type": solution_type,
        "implementation_model": implementation_model,
        "angle": angle,
        "freshness_reason": "Свежий внешний сигнал из новостей или кейсов, который можно привязать к знакомой бизнес-боли.",
        "signal_type": signal_type,
        "tools_mentioned": tools,
        "keywords": keywords,
        "source_urls": [source.url],
        "strategy_fit_score": strategy_fit,
        "business_relevance_score": relevance,
        "novelty_score": novelty,
        "priority_score": priority,
    }


async def _normalize_sources_with_llm(
    session: AsyncSession,
    *,
    product: Product,
    theme_override: str | None,
    sources: list[ResearchSource],
) -> list[dict[str, Any]]:
    if not sources:
        return []

    source_payload = [
        {
            "source_id": str(source.id),
            "title": source.title,
            "snippet": source.raw_snippet or "",
            "url": source.url,
            "published_at": source.published_at.isoformat() if source.published_at else None,
        }
        for source in sources
    ]

    system_prompt = """
You are a research normalization engine for a business-oriented AI content factory.
Your job is to transform raw external signals into structured topic candidates.
Stay strictly aligned with this strategy:
- The channel is about AI, bots, CRM and automation for small business, experts and small teams.
- Start from recognizable business pain.
- Use tools, releases and news only as fresh angles on a real business problem.
- Repeated pains are allowed if there is new value.
- Reject weak hype, generic AI chatter and empty trend summaries.

Return valid JSON with this exact shape:
{
  "candidates": [
    {
      "source_id": "uuid string",
      "title": "string",
      "summary": "string",
      "pain_cluster": "string",
      "audience_segment": "string",
      "business_process": "string",
      "solution_type": "string",
      "implementation_model": "string",
      "angle": "string",
      "freshness_reason": "string",
      "signal_type": "string",
      "tools_mentioned": ["string"],
      "keywords": ["string"],
      "source_urls": ["string"],
      "strategy_fit_score": 0,
      "business_relevance_score": 0,
      "novelty_score": 0,
      "priority_score": 0
    }
  ]
}
""".strip()

    user_prompt = f"""
Product name: {product.name}
Theme override: {theme_override or "not specified"}
Target audience: {product.target_audience or "not specified"}
Audience segments: {product.audience_segments}
Pain points: {product.pain_points}
Content pillars: {product.content_pillars}
Strategic goals: {product.strategic_goals}

Normalize these external signals into research candidates:
{source_payload}
""".strip()

    payload = await generate_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        session=session,
    )
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise LLMClientError("Research normalization returned invalid format.")
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _candidate_memory_key(candidate: ResearchCandidate | TopicMemory | dict[str, Any]) -> tuple[str, str, str, str, str]:
    if isinstance(candidate, (ResearchCandidate, TopicMemory)):
        return (
            candidate.pain_cluster,
            candidate.audience_segment,
            candidate.business_process,
            candidate.solution_type,
            candidate.angle,
        )
    return (
        str(candidate.get("pain_cluster") or ""),
        str(candidate.get("audience_segment") or ""),
        str(candidate.get("business_process") or ""),
        str(candidate.get("solution_type") or ""),
        str(candidate.get("angle") or ""),
    )


async def collect_research_candidates(
    session: AsyncSession,
    *,
    product: Product,
    theme_override: str | None = None,
    limit: int = 18,
) -> list[ResearchCandidate]:
    queries = _build_research_queries(product, theme_override=theme_override)
    fetched_payloads: list[dict[str, Any]] = []

    for query in queries:
        try:
            fetched_payloads.extend(await _fetch_google_news_rss(query))
        except Exception:
            continue

    deduped_payloads: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for payload in fetched_payloads:
        url = str(payload.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped_payloads.append(payload)
        if len(deduped_payloads) >= 40:
            break

    sources: list[ResearchSource] = []
    for payload in deduped_payloads:
        source = await _upsert_research_source(session, product_id=product.id, payload=payload)
        sources.append(source)
    await session.flush()

    existing_candidate_source_ids = set(
        (
            await session.execute(
                select(ResearchCandidate.source_id).where(
                    ResearchCandidate.product_id == product.id,
                    ResearchCandidate.source_id.is_not(None),
                )
            )
        ).scalars().all()
    )
    new_sources = [source for source in sources if source.id not in existing_candidate_source_ids]
    normalized_candidates: list[dict[str, Any]] = []
    if new_sources:
        try:
            normalized_candidates = await _normalize_sources_with_llm(
                session,
                product=product,
                theme_override=theme_override,
                sources=new_sources,
            )
        except LLMClientError:
            normalized_candidates = [_fallback_candidate_from_source(product, source) for source in new_sources]

        source_map = {str(source.id): source for source in new_sources}
        for candidate_payload in normalized_candidates:
            source_id = str(candidate_payload.get("source_id") or "").strip()
            source = source_map.get(source_id)
            if source is None:
                continue
            duplicate_group_key = _build_duplicate_group_key(
                _fit_label(candidate_payload.get("pain_cluster") or _guess_pain_cluster(source.title)),
                _fit_label(candidate_payload.get("audience_segment") or _guess_audience_segment(source.title, product)),
                _fit_label(candidate_payload.get("business_process") or _guess_business_process(source.title)),
                _fit_label(candidate_payload.get("solution_type") or _guess_solution_type(source.title)),
                _fit_label(candidate_payload.get("angle") or _guess_angle(source.title)),
            )
            candidate = ResearchCandidate(
                product_id=product.id,
                source_id=source.id,
                title=str(candidate_payload.get("title") or source.title).strip()[:500],
                summary=str(candidate_payload.get("summary") or source.raw_snippet or source.title).strip(),
                pain_cluster=_fit_label(candidate_payload.get("pain_cluster") or _guess_pain_cluster(source.title)),
                audience_segment=_fit_label(candidate_payload.get("audience_segment") or _guess_audience_segment(source.title, product)),
                business_process=_fit_label(candidate_payload.get("business_process") or _guess_business_process(source.title)),
                solution_type=_fit_label(candidate_payload.get("solution_type") or _guess_solution_type(source.title)),
                implementation_model=_fit_label(candidate_payload.get("implementation_model") or _guess_implementation_model(source.title)),
                angle=_fit_label(candidate_payload.get("angle") or _guess_angle(source.title)),
                freshness_reason=str(candidate_payload.get("freshness_reason") or "Fresh external signal."),
                signal_type=_fit_label(candidate_payload.get("signal_type") or _guess_signal_type(source.title), limit=50, fallback="new_solution"),
                tools_mentioned_json=[str(value) for value in candidate_payload.get("tools_mentioned", []) if str(value).strip()],
                keywords_json=[str(value) for value in candidate_payload.get("keywords", []) if str(value).strip()],
                source_urls_json=[str(value) for value in candidate_payload.get("source_urls", [source.url]) if str(value).strip()],
                strategy_fit_score=max(0, min(100, int(candidate_payload.get("strategy_fit_score") or 50))),
                business_relevance_score=max(0, min(100, int(candidate_payload.get("business_relevance_score") or 50))),
                novelty_score=max(0, min(100, int(candidate_payload.get("novelty_score") or 50))),
                priority_score=max(0, min(100, int(candidate_payload.get("priority_score") or 50))),
                duplicate_group_key=duplicate_group_key[:500],
                status="candidate",
            )
            session.add(candidate)
            source.status = "processed"

    if not normalized_candidates:
        for source in new_sources:
            source.status = "processed"

    await session.flush()

    recent_candidate_cutoff = datetime.now(timezone.utc) - timedelta(days=RESEARCH_WINDOW_DAYS)
    candidates_result = await session.execute(
        select(ResearchCandidate)
        .where(ResearchCandidate.product_id == product.id)
        .where(ResearchCandidate.created_at >= recent_candidate_cutoff)
        .where(ResearchCandidate.status.in_(("candidate", "approved", "used")))
        .order_by(ResearchCandidate.priority_score.desc(), ResearchCandidate.created_at.desc())
    )
    all_candidates = list(candidates_result.scalars().all())

    memory_cutoff = datetime.now(timezone.utc) - timedelta(days=MEMORY_WINDOW_DAYS)
    memory_result = await session.execute(
        select(TopicMemory)
        .where(TopicMemory.product_id == product.id)
        .where(TopicMemory.created_at >= memory_cutoff)
    )
    memory_entries = list(memory_result.scalars().all())
    memory_keys = {_candidate_memory_key(entry): entry for entry in memory_entries}

    filtered: list[ResearchCandidate] = []
    seen_candidate_groups: set[str] = set()
    pain_counts: dict[str, int] = {}

    for candidate in all_candidates:
        memory_key = _candidate_memory_key(candidate)
        memory_entry = memory_keys.get(memory_key)
        if memory_entry and memory_entry.status in {"published", "planned", "rejected"}:
            continue
        if candidate.duplicate_group_key in seen_candidate_groups:
            continue
        if pain_counts.get(candidate.pain_cluster, 0) >= 3:
            continue
        filtered.append(candidate)
        seen_candidate_groups.add(candidate.duplicate_group_key)
        pain_counts[candidate.pain_cluster] = pain_counts.get(candidate.pain_cluster, 0) + 1
        if len(filtered) >= limit:
            break

    return filtered


def build_research_candidate_block(candidates: list[ResearchCandidate]) -> str:
    if not candidates:
        return "No external research candidates available."

    lines: list[str] = []
    for candidate in candidates:
        lines.append(
            "\n".join(
                [
                    f"ID: {candidate.id}",
                    f"Title: {candidate.title}",
                    f"Summary: {candidate.summary}",
                    f"Pain cluster: {candidate.pain_cluster}",
                    f"Audience: {candidate.audience_segment}",
                    f"Business process: {candidate.business_process}",
                    f"Solution type: {candidate.solution_type}",
                    f"Implementation model: {candidate.implementation_model}",
                    f"Angle: {candidate.angle}",
                    f"Signal type: {candidate.signal_type}",
                    f"Freshness reason: {candidate.freshness_reason}",
                    f"Source URLs: {', '.join(candidate.source_urls_json[:3])}",
                ]
            )
        )
    return "\n\n".join(lines)


async def link_research_to_item(
    session: AsyncSession,
    *,
    plan: ContentPlan,
    item: ContentPlanItem,
    candidate_ids: list[uuid.UUID],
) -> None:
    if not candidate_ids:
        return

    existing_result = await session.execute(
        select(PlanResearchLink).where(
            PlanResearchLink.content_plan_item_id == item.id,
            PlanResearchLink.link_role == "primary_basis",
        )
    )
    existing_by_candidate = {link.research_candidate_id for link in existing_result.scalars().all()}
    for candidate_id in candidate_ids:
        if candidate_id in existing_by_candidate:
            continue
        session.add(
            PlanResearchLink(
                content_plan_id=plan.id,
                content_plan_item_id=item.id,
                research_candidate_id=candidate_id,
                link_role="primary_basis",
            )
        )


async def upsert_topic_memory_for_item(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    plan: ContentPlan,
    item: ContentPlanItem,
    candidate: ResearchCandidate | None = None,
) -> None:
    existing = await session.scalar(select(TopicMemory).where(TopicMemory.content_plan_item_id == item.id))
    research_data = item.research_data if isinstance(item.research_data, dict) else {}
    content_direction = str(research_data.get("content_direction") or item.article_type or "practical")

    pain_cluster = candidate.pain_cluster if candidate else str(research_data.get("pain_cluster") or "manual_routine")
    audience_segment = candidate.audience_segment if candidate else str(research_data.get("audience_segment") or "small_business")
    business_process = candidate.business_process if candidate else str(research_data.get("business_process") or "internal_ops")
    solution_type = candidate.solution_type if candidate else str(research_data.get("solution_type") or content_direction)
    implementation_model = candidate.implementation_model if candidate else str(research_data.get("implementation_model") or "ai_plus_workflow")
    angle = candidate.angle if candidate else str(research_data.get("angle") or content_direction)
    trigger_type = candidate.signal_type if candidate else str(research_data.get("trigger_type") or "evergreen")
    tools = candidate.tools_mentioned_json if candidate else [str(value) for value in research_data.get("tools_mentioned", []) if str(value).strip()]
    candidate_id = candidate.id if candidate else None

    payload = {
        "product_id": product_id,
        "content_plan_id": plan.id,
        "content_plan_item_id": item.id,
        "research_candidate_id": candidate_id,
        "title": item.title,
        "pain_cluster": pain_cluster,
        "audience_segment": audience_segment,
        "business_process": business_process,
        "solution_type": solution_type,
        "implementation_model": implementation_model,
        "angle": angle,
        "trigger_type": trigger_type,
        "tools_mentioned_json": tools,
        "novelty_signature": _build_novelty_signature(
            pain_cluster=pain_cluster,
            audience_segment=audience_segment,
            business_process=business_process,
            solution_type=solution_type,
            implementation_model=implementation_model,
            angle=angle,
        ),
        "status": item.status,
        "planned_at": item.scheduled_at if item.status in {"planned", "draft", "review-ready"} else None,
        "published_at": item.published_at if item.status == "published" else None,
    }

    if existing is None:
        session.add(TopicMemory(**payload))
        return

    for field_name, value in payload.items():
        setattr(existing, field_name, value)


async def sync_topic_memory_status_for_item(
    session: AsyncSession,
    *,
    item: ContentPlanItem,
) -> None:
    memory_entry = await session.scalar(select(TopicMemory).where(TopicMemory.content_plan_item_id == item.id))
    if memory_entry is None:
        return
    memory_entry.status = item.status
    memory_entry.planned_at = item.scheduled_at if item.status in {"planned", "draft", "review-ready"} else memory_entry.planned_at
    memory_entry.published_at = item.published_at if item.status == "published" else memory_entry.published_at
