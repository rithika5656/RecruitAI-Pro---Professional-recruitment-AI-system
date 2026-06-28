"""Validation helpers for generated submissions."""

from __future__ import annotations

import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(slots=True)
class SubmissionValidator:
    """Validate submissions against the supplied script and local checks."""

    validator_script: Path

    def validate(self, submission_path: Path) -> tuple[bool, str]:
        """Validate a generated submission file."""

        if self.validator_script.exists():
            completed = subprocess.run(
                [sys.executable, str(self.validator_script), str(submission_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            output = completed.stdout.strip() or completed.stderr.strip() or "validator completed"
            return completed.returncode == 0, output

        if submission_path.suffix.lower() == ".csv":
            dataframe = pd.read_csv(submission_path)
        else:
            dataframe = pd.read_excel(submission_path)
        required_columns = {"candidate_id", "rank", "score", "explanation"}
        missing = required_columns - set(dataframe.columns)
        if missing:
            return False, f"Missing columns: {sorted(missing)}"
        return True, "Local validation passed"
