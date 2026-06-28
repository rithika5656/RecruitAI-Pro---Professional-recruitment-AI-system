"""Domain models used across the ranking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class JobDescriptionProfile:
    """Structured representation of the job description."""

    raw_text: str
    title: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: float | None = None
    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    location: str = ""
    domain: str = ""
    responsibilities: list[str] = field(default_factory=list)
    preferred_qualifications: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CandidateProfile:
    """Normalized candidate profile loaded from the source dataset."""

    candidate_id: str
    raw: dict[str, Any]
    raw_text: str = ""
    name: str = ""
    location: str = ""
    headline: str = ""
    years_experience: float | None = None
    skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    domain_expertise: list[str] = field(default_factory=list)
    signals: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CandidateFeatures:
    """Feature vector inputs used for scoring and explanations."""

    candidate_id: str
    semantic_similarity: float = 0.0
    skill_overlap_ratio: float = 0.0
    experience_match_ratio: float = 0.0
    education_match_ratio: float = 0.0
    certification_match_ratio: float = 0.0
    signal_score: float = 0.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RankingResult:
    """Final ranking output for one candidate."""

    candidate_id: str
    overall_score: float
    rank: int = 0
    explanation: str = ""
    breakdown: dict[str, float] = field(default_factory=dict)
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
