from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document

from src.config import RankingWeights
from src.jd_parser import JobDescriptionParser
from src.models import CandidateFeatures, RankingResult
from src.preprocessing import Preprocessor
from src.ranking import RankingEngine
from src.submission import SubmissionBuilder
from src.validation import SubmissionValidator


def test_preprocessor_normalizes_candidate_record() -> None:
    preprocessor = Preprocessor()
    candidate = preprocessor.normalize_candidate(
        {
            "name": "  Jane Doe  ",
            "summary": "4 years of experience in Python and SQL.",
            "skills": "Python; SQL / C++",
            "education": ["Bachelor of Science in Computer Science"],
            "certifications": "AWS Certified Solutions Architect",
        },
        fallback_id="fallback-1",
    )

    assert candidate.candidate_id == "fallback-1"
    assert candidate.name == "Jane Doe"
    assert candidate.years_experience == 4.0
    assert candidate.skills == ["python", "sql", "cpp"]
    assert candidate.education == ["Bachelor of Science in Computer Science"]
    assert candidate.certifications == ["AWS Certified Solutions Architect"]
    assert preprocessor.validate_candidate(candidate) == []


def test_job_description_parser_extracts_core_requirements() -> None:
    parser = JobDescriptionParser()
    text = (
        "Senior Machine Learning Engineer\n"
        "Location: Remote\n"
        "We need 5 years of experience with Python, SQL, and machine learning.\n"
        "Responsibilities:\n"
        "- Build models\n"
        "- Ship experiments\n"
        "Preferred Qualifications:\n"
        "- Master\n"
        "- AWS Certified\n"
    )

    job = parser.parse(text)

    assert job.title == "Senior Machine Learning Engineer"
    assert job.location == "Remote"
    assert job.experience_years == 5.0
    assert "python" in job.skills
    assert "sql" in job.skills
    assert "machine learning" in job.skills
    assert job.responsibilities == ["- Build models", "- Ship experiments"]
    assert job.preferred_qualifications == ["- Master", "- AWS Certified"]


def test_ranking_engine_scores_and_orders_candidates() -> None:
    engine = RankingEngine(RankingWeights())
    candidate_features = {
        "c1": CandidateFeatures(candidate_id="c1", semantic_similarity=1.0, skill_overlap_ratio=0.5, experience_match_ratio=1.0),
        "c2": CandidateFeatures(candidate_id="c2", semantic_similarity=0.2, skill_overlap_ratio=0.2, experience_match_ratio=0.2),
    }
    candidates = [
        type("Candidate", (), {"candidate_id": "c1"})(),
        type("Candidate", (), {"candidate_id": "c2"})(),
    ]

    score, breakdown = engine.score_candidate(candidate_features["c1"])
    assert score == 75.0
    assert breakdown["semantic_similarity"] == 0.5

    ranked = engine.rank_candidates(candidates, candidate_features)
    assert [result.candidate_id for result in ranked] == ["c1", "c2"]
    assert [result.rank for result in ranked] == [1, 2]


def test_submission_export_and_validation(tmp_path: Path) -> None:
    builder = SubmissionBuilder()
    validator = SubmissionValidator(validator_script=tmp_path / "validate_submission.py")
    results = [
        RankingResult(candidate_id="c1", overall_score=91.2, rank=1, explanation="Top match"),
        RankingResult(candidate_id="c2", overall_score=82.4, rank=2, explanation="Second match"),
    ]

    output_path = builder.save_excel(results, tmp_path / "submission.xlsx")
    assert output_path.exists()

    frame = pd.read_excel(output_path)
    assert list(frame.columns) == ["candidate_id", "rank", "score", "explanation"]
    assert frame.loc[0, "candidate_id"] == "c1"

    is_valid, message = validator.validate(output_path)
    assert is_valid is True
    assert "Local validation passed" in message


def test_submission_builder_writes_csv(tmp_path: Path) -> None:
    builder = SubmissionBuilder()
    results = [RankingResult(candidate_id="c1", overall_score=95.0, rank=1, explanation="Great fit")]

    csv_path = builder.save_csv(results, tmp_path / "submission.csv")
    assert csv_path.exists()

    frame = pd.read_csv(csv_path)
    assert frame.loc[0, "candidate_id"] == "c1"


def test_docx_fixture_can_be_created(tmp_path: Path) -> None:
    document = Document()
    document.add_paragraph("Test Job Description")
    docx_path = tmp_path / "job_description.docx"
    document.save(docx_path)

    assert docx_path.exists()