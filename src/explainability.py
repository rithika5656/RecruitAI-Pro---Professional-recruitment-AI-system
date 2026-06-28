"""Human-readable explanation generation for ranking outputs."""

from __future__ import annotations

from dataclasses import dataclass

from .models import CandidateFeatures, CandidateProfile, JobDescriptionProfile, RankingResult


@dataclass(slots=True)
class ExplainabilityService:
    """Produce concise natural-language match explanations."""

    def build_explanation(
        self,
        candidate: CandidateProfile,
        job: JobDescriptionProfile,
        features: CandidateFeatures,
        result: RankingResult,
    ) -> str:
        """Create a readable explanation for a candidate ranking result."""

        matched_skills = ", ".join(features.matched_skills) if features.matched_skills else "None"
        missing_skills = ", ".join(features.missing_skills) if features.missing_skills else "None"
        required_exp = f"{job.experience_years:g} years" if job.experience_years is not None else "Not specified"
        found_exp = f"{candidate.years_experience:g} years" if candidate.years_experience is not None else "Not specified"

        lines = [
            f"Matched Skills: {matched_skills}",
            f"Experience Match: {required_exp} required, {found_exp} found",
            f"Education Match: {', '.join(candidate.education) if candidate.education else 'Not found'}",
            f"Missing Skills: {missing_skills}",
            f"Overall Score: {result.overall_score:.1f}",
        ]
        return "\n".join(lines)
