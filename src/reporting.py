"""Analytics helpers for the Streamlit dashboard and result summaries."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import pandas as pd

from .models import CandidateProfile, RankingResult


@dataclass(slots=True)
class AnalyticsService:
    """Build lightweight analytics outputs for the UI."""

    def results_dataframe(self, results: list[RankingResult]) -> pd.DataFrame:
        """Convert ranking results into a dataframe suitable for charts and tables."""

        return pd.DataFrame(
            [
                {
                    "candidate_id": result.candidate_id,
                    "rank": result.rank,
                    "score": result.overall_score,
                    "matched_skills": ", ".join(result.matched_skills),
                    "missing_skills": ", ".join(result.missing_skills),
                    "explanation": result.explanation,
                }
                for result in results
            ]
        )

    def score_summary(self, results: list[RankingResult]) -> dict[str, float]:
        """Return concise score statistics for the ranking dashboard."""

        if not results:
            return {"count": 0, "average_score": 0.0, "max_score": 0.0, "min_score": 0.0}

        scores = [result.overall_score for result in results]
        return {
            "count": float(len(scores)),
            "average_score": round(sum(scores) / len(scores), 2),
            "max_score": round(max(scores), 2),
            "min_score": round(min(scores), 2),
        }

    def skill_frequency(self, candidates: list[CandidateProfile], limit: int = 15) -> list[tuple[str, int]]:
        """Count the most common normalized skills across the candidate pool."""

        counter = Counter()
        for candidate in candidates:
            counter.update(candidate.skills)
        return counter.most_common(limit)
