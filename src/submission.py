"""Submission file generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .models import RankingResult


@dataclass(slots=True)
class SubmissionBuilder:
    """Generate hackathon submission artifacts."""

    def to_dataframe(self, results: list[RankingResult]) -> pd.DataFrame:
        """Convert ranking results to a tabular submission format."""

        return pd.DataFrame(
            [
                {
                    "candidate_id": result.candidate_id,
                    "rank": result.rank,
                    "score": result.overall_score,
                    "explanation": result.explanation,
                }
                for result in results
            ]
        )

    def save_excel(self, results: list[RankingResult], output_path: Path) -> Path:
        """Write the submission to an Excel workbook."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        dataframe = self.to_dataframe(results)
        dataframe.to_excel(output_path, index=False)
        return output_path

    def save_csv(self, results: list[RankingResult], output_path: Path) -> Path:
        """Write the submission to CSV."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        dataframe = self.to_dataframe(results)
        dataframe.to_csv(output_path, index=False)
        return output_path
