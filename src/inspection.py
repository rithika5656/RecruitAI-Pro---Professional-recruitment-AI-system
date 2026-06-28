"""Dataset inspection utilities for hackathon source files."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .loaders import LoadedDocument
from .utils import normalize_whitespace


@dataclass(slots=True)
class FieldSummary:
    """Summary statistics for one detected field in a dataset."""

    field_name: str
    inferred_type: str
    present_in_records: int
    missing_in_records: int
    examples: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DatasetReport:
    """Compact inspection report for a source file."""

    path: Path
    file_type: str
    record_count: int
    field_summaries: list[FieldSummary] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    preview: str = ""


class DatasetInspector:
    """Inspect raw inputs before they are normalized into the pipeline."""

    def inspect(self, document: LoadedDocument) -> DatasetReport:
        """Build a human-readable report for a loaded document."""

        content = document.content
        if isinstance(content, list):
            return self._inspect_records(document.path, document.file_type, content)
        if isinstance(content, dict):
            return self._inspect_mapping(document.path, document.file_type, content)
        return self._inspect_text(document.path, document.file_type, str(content))

    def _inspect_records(
        self,
        path: Path,
        file_type: str,
        records: list[Any],
    ) -> DatasetReport:
        """Inspect a record-based dataset such as JSONL or CSV."""

        dict_records = [record for record in records if isinstance(record, dict)]
        field_names = sorted({key for record in dict_records for key in record.keys()})
        summaries: list[FieldSummary] = []
        total_records = len(records)

        for field_name in field_names:
            values = [record.get(field_name) for record in dict_records]
            present_count = sum(value not in (None, "", []) for value in values)
            examples = self._collect_examples(values)
            summaries.append(
                FieldSummary(
                    field_name=field_name,
                    inferred_type=self._infer_type(values),
                    present_in_records=present_count,
                    missing_in_records=max(total_records - present_count, 0),
                    examples=examples,
                )
            )

        notes = [
            f"Detected {total_records} records.",
            f"Found {len(field_names)} fields across the sample.",
        ]
        preview = self._preview_records(dict_records)
        return DatasetReport(path=path, file_type=file_type, record_count=total_records, field_summaries=summaries, notes=notes, preview=preview)

    def _inspect_mapping(self, path: Path, file_type: str, payload: dict[str, Any]) -> DatasetReport:
        """Inspect a mapping-based JSON document such as a schema file."""

        summaries: list[FieldSummary] = []
        for key, value in payload.items():
            summaries.append(
                FieldSummary(
                    field_name=str(key),
                    inferred_type=self._infer_single(value),
                    present_in_records=1,
                    missing_in_records=0,
                    examples=self._collect_examples([value]),
                )
            )

        notes = [f"Detected {len(payload)} top-level keys."]
        preview = self._preview_mapping(payload)
        return DatasetReport(path=path, file_type=file_type, record_count=1, field_summaries=summaries, notes=notes, preview=preview)

    def _inspect_text(self, path: Path, file_type: str, text: str) -> DatasetReport:
        """Inspect free-form text documents such as DOCX exports."""

        cleaned_text = normalize_whitespace(text)
        notes = [
            f"Text length: {len(cleaned_text)} characters.",
            "Free-form document detected; semantic extraction is handled downstream.",
        ]
        preview = cleaned_text[:1000]
        return DatasetReport(path=path, file_type=file_type, record_count=0, notes=notes, preview=preview)

    def _collect_examples(self, values: list[Any], limit: int = 3) -> list[str]:
        """Collect compact human-readable value examples for a field."""

        examples: list[str] = []
        for value in values:
            if value in (None, "", []):
                continue
            text = normalize_whitespace(str(value))
            if text and text not in examples:
                examples.append(text)
            if len(examples) >= limit:
                break
        return examples

    def _infer_type(self, values: list[Any]) -> str:
        """Infer a field type from sampled values."""

        counter = Counter(self._infer_single(value) for value in values if value not in (None, "", []))
        if not counter:
            return "empty"
        return counter.most_common(1)[0][0]

    def _infer_single(self, value: Any) -> str:
        """Infer a type for one value."""

        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int) and not isinstance(value, bool):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "object"
        return "string"

    def _preview_records(self, records: list[dict[str, Any]]) -> str:
        """Create a short preview string for a tabular dataset."""

        if not records:
            return ""
        first_record = records[0]
        preview_items = [f"{key}: {normalize_whitespace(str(value))}" for key, value in list(first_record.items())[:10]]
        return "\n".join(preview_items)

    def _preview_mapping(self, payload: dict[str, Any]) -> str:
        """Create a preview string for a schema-like JSON payload."""

        preview_items = [f"{key}: {normalize_whitespace(str(value))}" for key, value in list(payload.items())[:10]]
        return "\n".join(preview_items)
