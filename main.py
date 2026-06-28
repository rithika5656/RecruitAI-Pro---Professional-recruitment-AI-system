"""Command-line entry point for the ranking pipeline."""

from __future__ import annotations

from src.pipeline import CandidateDiscoveryPipeline


def main() -> None:
    """Run the pipeline using files from the raw data directory."""

    pipeline = CandidateDiscoveryPipeline()
    raw_dir = pipeline.config.raw_data_dir
    jd_path = raw_dir / "job_description.docx"
    candidates_path = raw_dir / "candidates.jsonl"

    if not jd_path.exists() or not candidates_path.exists():
        raise FileNotFoundError(
            "Place job_description.docx and candidates.jsonl under data/raw before running the pipeline."
        )

    jd_profile, candidates = pipeline.load_inputs(jd_path, candidates_path)
    results = pipeline.rank(jd_profile, candidates)
    output_path = pipeline.generate_submission(results)
    is_valid, message = pipeline.validator.validate(output_path)
    print(f"Submission saved to: {output_path}")
    print(f"Validation: {is_valid} - {message}")


if __name__ == "__main__":
    main()
