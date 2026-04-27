from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models import Product


DZEN_FORMAT_MODES = {"auto", "post", "article"}


def normalize_dzen_format_mode(raw_value: Any) -> str:
    value = str(raw_value or "").strip().lower()
    if value in DZEN_FORMAT_MODES:
        return value
    return "auto"


def resolve_dzen_format_mode(product: "Product | None", item_research_data: dict[str, Any] | None = None) -> str:
    if isinstance(item_research_data, dict):
        stored_mode = normalize_dzen_format_mode(item_research_data.get("dzen_format_mode"))
        if stored_mode in DZEN_FORMAT_MODES:
            return stored_mode

    if product is not None:
        for channel in getattr(product, "channels", []) or []:
            if getattr(channel, "platform", "").strip().lower() != "dzen":
                continue
            return normalize_dzen_format_mode(getattr(channel, "settings_json", {}).get("content_mode"))

    return "auto"


def resolve_dzen_output_format(content_direction: str | None, dzen_format_mode: str) -> str:
    normalized_mode = normalize_dzen_format_mode(dzen_format_mode)
    if normalized_mode == "post":
        return "dzen_post"
    if normalized_mode == "article":
        return "dzen_article"

    normalized_direction = str(content_direction or "").strip().lower()
    if normalized_direction in {"news", "opinion", "critical"}:
        return "dzen_post"
    return "dzen_article"
