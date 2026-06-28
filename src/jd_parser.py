"""Job description understanding and extraction logic."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import JobDescriptionProfile
from .utils import extract_years_of_experience, normalize_whitespace, unique_preserve_order


SECTION_PATTERNS = {
    "responsibilities": re.compile(r"(?:responsibilities|what you will do|duties)[:\-]?\s*(.+?)(?=\n\w|\Z)", re.IGNORECASE | re.DOTALL),
    "preferred": re.compile(r"(?:preferred qualifications|nice to have|preferred)[:\-]?\s*(.+?)(?=\n\w|\Z)", re.IGNORECASE | re.DOTALL),
}

SKILL_TERMS = [
    "python",
    "sql",
    "machine learning",
    "deep learning",
    "nlp",
    "data analysis",
    "statistics",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "scikit-learn",
]


@dataclass(slots=True)
class JobDescriptionParser:
    """Extract structured requirements from free-form JD text."""

    def parse(self, text: str) -> JobDescriptionProfile:
        """Parse the supplied job description text into a structured profile."""

        cleaned_text = normalize_whitespace(text)
        return JobDescriptionProfile(
            raw_text=cleaned_text,
            title=self._extract_title(cleaned_text),
            skills=self._extract_skills(cleaned_text),
            experience_years=extract_years_of_experience(cleaned_text),
            education=self._extract_keywords(cleaned_text, ["bachelor", "master", "phd", "degree"]),
            certifications=self._extract_keywords(cleaned_text, ["certification", "certified", "pmp", "aws certified"]),
            location=self._extract_location(cleaned_text),
            domain=self._extract_domain(cleaned_text),
            responsibilities=self._extract_section(cleaned_text, "responsibilities"),
            preferred_qualifications=self._extract_section(cleaned_text, "preferred"),
        )

    def _extract_title(self, text: str) -> str:
        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        return first_line[:120]

    def _extract_skills(self, text: str) -> list[str]:
        found = [skill for skill in SKILL_TERMS if skill in text.lower()]
        return unique_preserve_order(found)

    def _extract_keywords(self, text: str, keywords: list[str]) -> list[str]:
        lower = text.lower()
        return unique_preserve_order(keyword for keyword in keywords if keyword in lower)

    def _extract_location(self, text: str) -> str:
        match = re.search(r"\b(?:location|remote|hybrid)[:\-]?\s*([A-Za-z0-9,\- ]{2,80})", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_domain(self, text: str) -> str:
        domain_terms = ["finance", "healthcare", "retail", "banking", "edtech", "saas", "ecommerce", "ai", "ml"]
        lower = text.lower()
        for term in domain_terms:
            if term in lower:
                return term
        return ""

    def _extract_section(self, text: str, section_name: str) -> list[str]:
        pattern = SECTION_PATTERNS[section_name]
        match = pattern.search(text)
        if not match:
            return []
        section_text = match.group(1)
        items = [line.strip("-• \t") for line in section_text.splitlines() if line.strip()]
        return unique_preserve_order(items)
