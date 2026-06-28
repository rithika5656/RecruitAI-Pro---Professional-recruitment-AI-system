"""Application configuration and default paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RankingWeights:
    """Weights used by the scoring engine."""

    semantic_similarity: float = 0.50
    skill_match: float = 0.20
    experience_match: float = 0.15
    education: float = 0.05
    certifications: float = 0.05
    additional_signals: float = 0.05

    def normalized(self) -> "RankingWeights":
        """Return a copy normalized to sum to 1.0."""

        total = (
            self.semantic_similarity
            + self.skill_match
            + self.experience_match
            + self.education
            + self.certifications
            + self.additional_signals
        )
        if total <= 0:
            return RankingWeights()

        return RankingWeights(
            semantic_similarity=self.semantic_similarity / total,
            skill_match=self.skill_match / total,
            experience_match=self.experience_match / total,
            education=self.education / total,
            certifications=self.certifications / total,
            additional_signals=self.additional_signals / total,
        )


@dataclass(slots=True)
class AppConfig:
    """Centralized configuration for file paths and runtime settings."""

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    data_dir: Path = field(init=False)
    raw_data_dir: Path = field(init=False)
    processed_data_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    embeddings_model_name: str = "all-MiniLM-L6-v2"
    weights: RankingWeights = field(default_factory=RankingWeights)

    def __post_init__(self) -> None:
        self.data_dir = self.project_root / "data"
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.models_dir = self.project_root / "models"
        self.output_dir = self.project_root / "output"
