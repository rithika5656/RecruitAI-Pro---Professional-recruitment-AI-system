"""Utility helpers shared across the project."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


SKILL_SPLIT_PATTERN = re.compile(r"[;,/|\n]")
MULTISPACE_PATTERN = re.compile(r"\s+")
EXPERIENCE_PATTERN = re.compile(
    r"(?P<years>\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?|yr)"
    r"(?:\s+of)?\s+(?:experience)?",
    re.IGNORECASE,
)


def read_text_file(path: Path) -> str:
    """Read a UTF-8 text file with graceful fallback."""

    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> Any:
    """Load JSON from disk."""

    return json.loads(read_text_file(path))


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim edges."""

    return MULTISPACE_PATTERN.sub(" ", text).strip()


def normalize_skill_name(skill: str) -> str:
    """Normalize a skill string for matching."""

    skill = normalize_whitespace(skill).lower()
    return skill.replace("c++", "cpp").replace("c#", "csharp")


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    """Deduplicate strings while preserving input order."""

    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Convert a value to float when possible."""

    if value is None:
        return default
    try:
        result = float(value)
        if math.isnan(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def extract_years_of_experience(text: str) -> float | None:
    """Extract the first experience figure from free text."""

    match = EXPERIENCE_PATTERN.search(text)
    if match:
        return safe_float(match.group("years"), default=None)
    return None


def split_skill_text(text: str) -> list[str]:
    """Split a semi-structured skill field into tokens."""

    parts = [segment.strip() for segment in SKILL_SPLIT_PATTERN.split(text)]
    return unique_preserve_order(parts)
