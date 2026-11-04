"""Phase 7B Innovation Analyzer package."""

from app.services.innovation.profile import (
    EvidenceType,
    FeatureEvidence,
    ProjectProfile,
)
from app.services.innovation.extractor import ProjectProfileExtractor
from app.services.innovation.cohort_comparison import (
    CohortComparisonService,
    SimpleTfidfVectorizer,
)
from app.services.innovation.scoring import (
    InnovationScoringEngine,
    RULES_VERSION,
    CATEGORY_INSUFFICIENT_EVIDENCE,
    CATEGORY_LIMITED_DIFFERENTIATION,
    CATEGORY_SOME_DISTINCTIVE,
    CATEGORY_STRONG_DISTINCTIVE,
    CATEGORY_FACULTY_REVIEW,
)
from app.services.innovation.analyzer import InnovationAnalyzer
from app.services.innovation.service import InnovationService

__all__ = [
    "EvidenceType",
    "FeatureEvidence",
    "ProjectProfile",
    "ProjectProfileExtractor",
    "CohortComparisonService",
    "SimpleTfidfVectorizer",
    "InnovationScoringEngine",
    "RULES_VERSION",
    "CATEGORY_INSUFFICIENT_EVIDENCE",
    "CATEGORY_LIMITED_DIFFERENTIATION",
    "CATEGORY_SOME_DISTINCTIVE",
    "CATEGORY_STRONG_DISTINCTIVE",
    "CATEGORY_FACULTY_REVIEW",
    "InnovationAnalyzer",
    "InnovationService",
]

