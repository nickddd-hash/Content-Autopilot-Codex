from __future__ import annotations

import re


_MOJIBAKE_MARKERS = (
    "\u00d0",
    "\u00d1",
    "\u0420\u045f",
    "\u0420\u00b0",
    "\u0420\u00b5",
    "\u0420\u00b8",
    "\u0420\u00be",
    "\u0421\u0403",
    "\u0421\u201a",
    "\u0432\u20ac",
    "\u00c2",
)

_NOISE_CHARS = {
    "\u00d0",
    "\u00d1",
    "\u00c2",
    "\u00c3",
    "\ufffd",
}


def _is_cyrillic(char: str) -> bool:
    return ("\u0410" <= char <= "\u044f") or char in {"\u0401", "\u0451"}


def _text_quality_score(value: str) -> int:
    cyrillic_count = sum(1 for char in value if _is_cyrillic(char))
    mojibake_hits = sum(value.count(marker) for marker in _MOJIBAKE_MARKERS)
    noise_count = sum(1 for char in value if char in _NOISE_CHARS)
    return (cyrillic_count * 2) - (mojibake_hits * 3) - (noise_count * 2)


def repair_common_mojibake(value: str) -> str:
    if not value:
        return value

    current = value

    for _ in range(3):
        best_candidate = current
        best_score = _text_quality_score(current)

        for source_encoding in ("cp1251", "cp1252", "latin1"):
            try:
                candidate = current.encode(source_encoding).decode("utf-8")
            except UnicodeError:
                continue

            candidate_score = _text_quality_score(candidate)
            if candidate_score > best_score:
                best_candidate = candidate
                best_score = candidate_score

        if best_candidate == current:
            break
        current = best_candidate

    return current


def normalize_user_facing_text(value: str) -> str:
    repaired = repair_common_mojibake(value)
    cleaned = (
        repaired.replace("\u0432\u20ac\u201d", "-")
        .replace("\u0432\u20ac\u201c", "-")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u00A0", " ")
    )
    cleaned = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\*\s+", "- ", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "")
    cleaned = re.sub(r"(?<!\w)\*(?=\S)|(?<=\S)\*(?!\w)", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
