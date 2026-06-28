"""Formatting utilities for dataset inspection reports."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .inspection import DatasetReport


class InspectionReporter:
    """Render dataset inspection results for humans or downstream tools."""

    def build_markdown_report(self, reports: list[DatasetReport]) -> str:
        """Convert inspection results into a readable markdown document."""

        lines: list[str] = ["# Dataset Inspection Report", ""]
        for report in reports:
            lines.extend(
                [
                    f"## {report.path.name}",
                    f"- Path: {report.path}",
                    f"- Type: {report.file_type}",
                    f"- Records: {report.record_count}",
                ]
            )
            if report.notes:
                lines.append("- Notes:")
                lines.extend(f"  - {note}" for note in report.notes)
            if report.field_summaries:
                lines.extend(["", "| Field | Type | Present | Missing | Examples |", "| --- | --- | ---: | ---: | --- |"])
                for field in report.field_summaries:
                    examples = "; ".join(field.examples) if field.examples else ""
                    lines.append(
                        f"| {field.field_name} | {field.inferred_type} | {field.present_in_records} | {field.missing_in_records} | {examples} |"
                    )
            if report.preview:
                lines.extend(["", "```text", report.preview, "```", ""])
            else:
                lines.append("")
        return "\n".join(lines).strip() + "\n"

    def build_json_report(self, reports: list[DatasetReport]) -> list[dict[str, Any]]:
        """Convert inspection results into JSON-serializable dictionaries."""

        return [asdict(report) for report in reports]

    def save(self, reports: list[DatasetReport], output_path: Path) -> Path:
        """Persist the report using markdown or JSON based on the file extension."""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() == ".json":
            output_path.write_text(json.dumps(self.build_json_report(reports), indent=2), encoding="utf-8")
        else:
            output_path.write_text(self.build_markdown_report(reports), encoding="utf-8")
        return output_path