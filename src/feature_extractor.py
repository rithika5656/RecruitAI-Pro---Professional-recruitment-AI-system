"""Candidate feature extraction for ranking and explanations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import CandidateFeatures, CandidateProfile, JobDescriptionProfile
from .utils import normalize_skill_name, unique_preserve_order


@dataclass(slots=True)
class FeatureExtractor:
    """Build comparable features from JD and candidate data."""

    def extract(self, candidate: CandidateProfile, job: JobDescriptionProfile) -> CandidateFeatures:
        """Derive match features between a candidate and the job description."""

        candidate_skills = self._normalize_items(candidate.skills + candidate.domain_expertise + candidate.soft_skills)
        job_skills = self._normalize_items(job.skills)
        matched_skills = [skill for skill in job_skills if skill in candidate_skills]
        missing_skills = [skill for skill in job_skills if skill not in candidate_skills]

        skill_overlap_ratio = len(matched_skills) / max(len(job_skills), 1)
        experience_match_ratio = self._experience_match(candidate.years_experience, job.experience_years)
        education_match_ratio = self._keyword_match(candidate.education, job.education)
        certification_match_ratio = self._keyword_match(candidate.certifications, job.certifications)

        return CandidateFeatures(
            candidate_id=candidate.candidate_id,
            skill_overlap_ratio=skill_overlap_ratio,
            experience_match_ratio=experience_match_ratio,
            education_match_ratio=education_match_ratio,
            certification_match_ratio=certification_match_ratio,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

    def _normalize_items(self, values: Iterable[str]) -> list[str]:
        """Normalize and deduplicate text items."""

        return unique_preserve_order(normalize_skill_name(value) for value in values if value)

    def _keyword_match(self, candidate_items: list[str], job_items: list[str]) -> float:
        """Measure overlap between two keyword lists."""

        if not job_items:
            return 1.0
        normalized_candidate = set(self._normalize_items(candidate_items))
        normalized_job = set(self._normalize_items(job_items))
        if not normalized_job:
            return 1.0
        return len(normalized_candidate & normalized_job) / len(normalized_job)

    def _experience_match(self, candidate_years: float | None, job_years: float | None) -> float:
        """Score experience fit against the minimum requirement."""

        if job_years is None:
            return 1.0
        if candidate_years is None:
            return 0.0
        if candidate_years >= job_years:
            return 1.0
        return max(candidate_years / max(job_years, 1.0), 0.0)
