"""Data cleaning and normalization for candidate records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .models import CandidateProfile
from .utils import (
    extract_years_of_experience,
    normalize_skill_name,
    normalize_whitespace,
    split_skill_text,
    unique_preserve_order,
)


@dataclass(slots=True)
class SchemaFieldMap:
    """Flexible schema mapping to support unknown candidate sources."""

    candidate_id: str = "candidate_id"
    name: str = "name"
    location: str = "location"
    headline: str = "headline"
    raw_text: str = "summary"
    skills: str = "skills"
    soft_skills: str = "soft_skills"
    education: str = "education"
    certifications: str = "certifications"
    projects: str = "projects"
    domain_expertise: str = "domain_expertise"
    years_experience: str = "years_experience"


class Preprocessor:
    """Normalize raw candidate records into structured profiles."""

    def __init__(self, field_map: SchemaFieldMap | None = None) -> None:
        self.field_map = field_map or SchemaFieldMap()

    def normalize_candidate(self, record: dict[str, Any], fallback_id: str) -> CandidateProfile:
        """Convert a raw candidate dictionary to a normalized profile."""

        candidate_id = self._get_str(record, self.field_map.candidate_id, fallback_id)
        raw_text = self._get_str(record, self.field_map.raw_text, "")
        years_experience = self._get_float(record, self.field_map.years_experience)
        if years_experience is None:
            years_experience = extract_years_of_experience(raw_text)

        return CandidateProfile(
            candidate_id=candidate_id,
            raw=record,
            raw_text=normalize_whitespace(raw_text),
            name=self._get_str(record, self.field_map.name, ""),
            location=self._get_str(record, self.field_map.location, ""),
            headline=self._get_str(record, self.field_map.headline, ""),
            years_experience=years_experience,
            skills=self._normalize_list_field(record.get(self.field_map.skills, []), normalize_as_skill=True),
            soft_skills=self._normalize_list_field(record.get(self.field_map.soft_skills, []), normalize_as_skill=True),
            education=self._normalize_list_field(record.get(self.field_map.education, [])),
            certifications=self._normalize_list_field(record.get(self.field_map.certifications, [])),
            projects=self._normalize_list_field(record.get(self.field_map.projects, [])),
            domain_expertise=self._normalize_list_field(record.get(self.field_map.domain_expertise, [])),
            metadata={k: v for k, v in record.items() if k not in self._field_values()},
        )

    def normalize_candidates(self, records: Iterable[dict[str, Any]]) -> list[CandidateProfile]:
        """Normalize many candidate records."""

        return [self.normalize_candidate(record, fallback_id=str(index + 1)) for index, record in enumerate(records)]

    def validate_candidate(self, candidate: CandidateProfile) -> list[str]:
        """Return validation warnings for a candidate profile."""

        warnings: list[str] = []
        if not candidate.candidate_id:
            warnings.append("missing_candidate_id")
        if not candidate.raw_text and not candidate.skills and not candidate.headline:
            warnings.append("insufficient_profile_content")
        if candidate.years_experience is not None and candidate.years_experience < 0:
            warnings.append("invalid_experience")
        return warnings

    def _field_values(self) -> set[str]:
        return {
            self.field_map.candidate_id,
            self.field_map.name,
            self.field_map.location,
            self.field_map.headline,
            self.field_map.raw_text,
            self.field_map.skills,
            self.field_map.soft_skills,
            self.field_map.education,
            self.field_map.certifications,
            self.field_map.projects,
            self.field_map.domain_expertise,
            self.field_map.years_experience,
        }

    def _normalize_list_field(self, value: Any, normalize_as_skill: bool = False) -> list[str]:
        """Convert any semi-structured field into a normalized string list."""

        if value is None:
            return []
        if isinstance(value, str):
            values = split_skill_text(value) if any(sep in value for sep in [";", ",", "/", "|"]) else [value.strip()]
            return unique_preserve_order(
                normalize_skill_name(part) if normalize_as_skill else normalize_whitespace(part)
                for part in values
                if part
            )
        if isinstance(value, list):
            items: list[str] = []
            for entry in value:
                if isinstance(entry, str):
                    items.extend(split_skill_text(entry) if ";" in entry or "," in entry else [entry.strip()])
                else:
                    items.append(str(entry).strip())
            return unique_preserve_order(
                normalize_skill_name(item) if normalize_as_skill else normalize_whitespace(item)
                for item in items
                if item
            )
        return [normalize_skill_name(str(value)) if normalize_as_skill else normalize_whitespace(str(value))]

    def _get_str(self, record: dict[str, Any], key: str, default: str) -> str:
        value = record.get(key, default)
        if value is None:
            return default
        return normalize_whitespace(str(value))

    def _get_float(self, record: dict[str, Any], key: str) -> float | None:
        value = record.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
