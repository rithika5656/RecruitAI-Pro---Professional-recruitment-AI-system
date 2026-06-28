"""End-to-end orchestration for the candidate ranking workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import AppConfig
from .embeddings import EmbeddingService
from .explainability import ExplainabilityService
from .feature_extractor import FeatureExtractor
from .jd_parser import JobDescriptionParser
from .loaders import DataLoader
from .models import CandidateFeatures, CandidateProfile, JobDescriptionProfile, RankingResult
from .preprocessing import Preprocessor
from .ranking import RankingEngine
from .submission import SubmissionBuilder
from .validation import SubmissionValidator


@dataclass(slots=True)
class CandidateDiscoveryPipeline:
    """Coordinate loading, parsing, ranking, explaining, and exporting."""

    config: AppConfig = field(default_factory=AppConfig)
    loader: DataLoader = field(default_factory=DataLoader)
    preprocessor: Preprocessor = field(default_factory=Preprocessor)
    jd_parser: JobDescriptionParser = field(default_factory=JobDescriptionParser)
    feature_extractor: FeatureExtractor = field(default_factory=FeatureExtractor)
    embedding_service: EmbeddingService = field(init=False)
    ranking_engine: RankingEngine = field(init=False)
    explainability_service: ExplainabilityService = field(default_factory=ExplainabilityService)
    submission_builder: SubmissionBuilder = field(default_factory=SubmissionBuilder)
    validator: SubmissionValidator = field(init=False)

    def __post_init__(self) -> None:
        self.embedding_service = EmbeddingService(self.config.embeddings_model_name)
        self.ranking_engine = RankingEngine(self.config.weights)
        self.validator = SubmissionValidator(self.config.project_root / "validate_submission.py")

    def load_inputs(self, jd_path: Path, candidates_path: Path) -> tuple[JobDescriptionProfile, list[CandidateProfile]]:
        """Load and normalize the job description and candidate dataset."""

        jd_document = self.loader.load(jd_path)
        candidates_document = self.loader.load(candidates_path)
        jd_profile = self.jd_parser.parse(str(jd_document.content))
        raw_candidates = candidates_document.content if isinstance(candidates_document.content, list) else []
        candidates = self.preprocessor.normalize_candidates(raw_candidates)
        return jd_profile, candidates

    def rank(self, jd_profile: JobDescriptionProfile, candidates: list[CandidateProfile]) -> list[RankingResult]:
        """Score and rank all candidates for a given JD."""

        candidate_features: dict[str, CandidateFeatures] = {}
        job_embedding = self.embedding_service.embed(jd_profile.raw_text)

        for candidate in candidates:
            features = self.feature_extractor.extract(candidate, jd_profile)
            candidate_embedding = self.embedding_service.embed(candidate.raw_text or candidate.headline or candidate.name)
            features.semantic_similarity = self.ranking_engine.semantic_similarity(candidate_embedding, job_embedding)
            candidate_features[candidate.candidate_id] = features

        results = self.ranking_engine.rank_candidates(candidates, candidate_features)
        for result in results:
            candidate = next(item for item in candidates if item.candidate_id == result.candidate_id)
            features = candidate_features[result.candidate_id]
            result.explanation = self.explainability_service.build_explanation(candidate, jd_profile, features, result)
        return results

    def generate_submission(self, results: list[RankingResult], output_dir: Path | None = None) -> Path:
        """Export ranking results as the expected submission workbook."""

        destination_dir = output_dir or self.config.output_dir
        submission_path = destination_dir / "submission.xlsx"
        self.submission_builder.save_excel(results, submission_path)
        return submission_path
