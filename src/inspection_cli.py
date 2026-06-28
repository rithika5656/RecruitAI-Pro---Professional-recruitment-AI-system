"""Command-line tooling for automatic dataset inspection reports."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .config import AppConfig
from .inspection import DatasetInspector, DatasetReport
from .inspection_reporting import InspectionReporter
from .loaders import DataLoader


SUPPORTED_SUFFIXES = {".json", ".jsonl", ".csv", ".docx"}


@dataclass(slots=True)
class InspectionCLIResult:
    """Return value for the inspection workflow."""

    reports: list[DatasetReport]
    output_path: Path | None


def discover_input_files(input_dir: Path) -> list[Path]:
    """Find supported source files in a directory."""

    if not input_dir.exists():
        return []
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def inspect_input_directory(input_dir: Path) -> list[DatasetReport]:
    """Load every supported file in a directory and summarize it."""

    loader = DataLoader()
    inspector = DatasetInspector()
    reports: list[DatasetReport] = []

    for path in discover_input_files(input_dir):
        try:
            loaded_document = loader.load(path)
            reports.append(inspector.inspect(loaded_document))
        except Exception as exc:  # pragma: no cover - defensive path for bad source files
            reports.append(
                DatasetReport(
                    path=path,
                    file_type=path.suffix.lstrip("."),
                    record_count=0,
                    notes=[f"Failed to inspect file: {exc}"],
                )
            )
    return reports


def build_report(input_dir: Path, output_path: Path | None = None) -> InspectionCLIResult:
    """Generate and optionally persist an inspection report."""

    reports = inspect_input_directory(input_dir)
    reporter = InspectionReporter()

    if output_path is not None:
        reporter.save(reports, output_path)

    return InspectionCLIResult(reports=reports, output_path=output_path)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    config = AppConfig()
    parser = argparse.ArgumentParser(description="Inspect hackathon source files and generate a summary report.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=config.raw_data_dir,
        help="Directory containing the uploaded source files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.output_dir / "inspection_report.md",
        help="Where to write the report. Use a .json extension for structured output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for dataset inspection."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    result = build_report(args.input_dir, args.output)
    reporter = InspectionReporter()
    markdown = reporter.build_markdown_report(result.reports)
    print(markdown)
    if result.output_path is not None:
        print(f"Report written to: {result.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())