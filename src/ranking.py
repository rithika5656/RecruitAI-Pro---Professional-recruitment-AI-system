"""Weighted candidate ranking engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .config import RankingWeights
from .models import CandidateFeatures, CandidateProfile, RankingResult


@dataclass(slots=True)
class RankingEngine:
    """Combine semantic and structured signals into a final score."""

    weights: RankingWeights

    def score_candidate(self, features: CandidateFeatures) -> tuple[float, dict[str, float]]:
        """Compute the weighted score for one candidate."""

        weights = self.weights.normalized()
        semantic = self._clip(features.semantic_similarity)
        skill = self._clip(features.skill_overlap_ratio)
        experience = self._clip(features.experience_match_ratio)
        education = self._clip(features.education_match_ratio)
        certifications = self._clip(features.certification_match_ratio)
        signals = self._clip(features.signal_score)

        breakdown = {
            "semantic_similarity": semantic * weights.semantic_similarity,
            "skill_match": skill * weights.skill_match,
            "experience_match": experience * weights.experience_match,
            "education": education * weights.education,
            "certifications": certifications * weights.certifications,
            "additional_signals": signals * weights.additional_signals,
        }
        return round(sum(breakdown.values()) * 100, 4), breakdown

    def rank_candidates(
        self,
        candidates: Iterable[CandidateProfile],
        features: dict[str, CandidateFeatures],
    ) -> list[RankingResult]:
        """Rank all candidates by their computed score."""

        results: list[RankingResult] = []
        for candidate in candidates:
            candidate_features = features[candidate.candidate_id]
            score, breakdown = self.score_candidate(candidate_features)
            results.append(
                RankingResult(
                    candidate_id=candidate.candidate_id,
                    overall_score=score,
                    breakdown=breakdown,
                    matched_skills=candidate_features.matched_skills,
                    missing_skills=candidate_features.missing_skills,
                )
            )

        results.sort(key=lambda result: result.overall_score, reverse=True)
        for index, result in enumerate(results, start=1):
            result.rank = index
        return results

    def semantic_similarity(self, candidate_embedding: np.ndarray, job_embedding: np.ndarray) -> float:
        """Calculate cosine similarity between normalized embeddings."""

        numerator = float(np.dot(candidate_embedding, job_embedding))
        denominator = float(np.linalg.norm(candidate_embedding) * np.linalg.norm(job_embedding))
        if denominator == 0:
            return 0.0
        return self._clip(numerator / denominator)

    def _clip(self, value: float) -> float:
        return float(np.clip(value, 0.0, 1.0))
