"""Deterministic distinctiveness and innovation assessment engine (Phase 7B).

Calculates multi-dimensional distinctiveness across problem, solution, features,
technical contribution, and evidence quality. Never generates arbitrary global
novelty percentages or assigns a high innovation score to an empty cohort.
"""

from typing import Any, Dict, List, Tuple
from app.services.innovation.profile import EvidenceType, ProjectProfile

RULES_VERSION = "v1.0-deterministic-rubric"

# Advisory Category Constants
CATEGORY_INSUFFICIENT_EVIDENCE = "Insufficient Evidence"
CATEGORY_LIMITED_DIFFERENTIATION = "Limited Differentiation"
CATEGORY_SOME_DISTINCTIVE = "Some Distinctive Elements"
CATEGORY_STRONG_DISTINCTIVE = "Strong Distinctive Elements"
CATEGORY_FACULTY_REVIEW = "Faculty Review Required"


class InnovationScoringEngine:
    """Computes transparent distinctiveness metrics and advisory categories."""

    @classmethod
    def evaluate(
        cls,
        profile: ProjectProfile,
        cohort_size: int,
        matches: List[Dict[str, Any]],
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """
        Evaluate distinctiveness and assign an advisory category.

        Returns:
            Tuple of (advisory_category, dimension_scores, limitations_list)
        """
        limitations: List[str] = []

        # 1. Handle Empty or Insufficient Project Profile
        if profile.is_empty:
            limitations.append("Project contains no source files or indexable files.")
            return CATEGORY_INSUFFICIENT_EVIDENCE, cls._empty_scores(), limitations

        if not profile.is_sufficient:
            limitations.append("Project profile has insufficient information to assess innovation.")
            return CATEGORY_INSUFFICIENT_EVIDENCE, cls._empty_scores(), limitations

        # 2. Handle Empty Cohort
        if cohort_size == 0:
            limitations.append(
                "No comparable cohort submissions are available in PostgreSQL to assess distinctiveness. "
                "Distinctiveness cannot be determined without peer comparisons."
            )
            scores = {
                "problem_distinctiveness": 0.0,
                "solution_distinctiveness": 0.0,
                "feature_differentiation": 0.0,
                "technical_contribution": cls._calculate_technical_contribution(profile),
                "evidence_supporting_claim": cls._calculate_evidence_quality(profile),
                "max_cohort_similarity": 0.0,
                "average_cohort_similarity": 0.0,
            }
            return CATEGORY_INSUFFICIENT_EVIDENCE, scores, limitations

        # 3. Calculate dimension-wise similarity and distinctiveness
        max_overall_sim = max((m.get("overall_similarity", 0.0) for m in matches), default=0.0)
        avg_overall_sim = sum(m.get("overall_similarity", 0.0) for m in matches) / max(1, len(matches))

        max_problem_sim = max((m.get("problem_similarity", 0.0) for m in matches), default=0.0)
        max_solution_sim = max((m.get("solution_similarity", 0.0) for m in matches), default=0.0)
        max_feature_sim = max((m.get("feature_similarity", 0.0) for m in matches), default=0.0)

        problem_dist = round(max(0.0, min(1.0, 1.0 - max_problem_sim)), 4)
        solution_dist = round(max(0.0, min(1.0, 1.0 - max_solution_sim)), 4)
        feature_diff = round(max(0.0, min(1.0, 1.0 - max_feature_sim)), 4)

        tech_contrib = cls._calculate_technical_contribution(profile)
        evidence_quality = cls._calculate_evidence_quality(profile)

        scores = {
            "problem_distinctiveness": problem_dist,
            "solution_distinctiveness": solution_dist,
            "feature_differentiation": feature_diff,
            "technical_contribution": tech_contrib,
            "evidence_supporting_claim": evidence_quality,
            "max_cohort_similarity": round(max_overall_sim, 4),
            "average_cohort_similarity": round(avg_overall_sim, 4),
        }

        # 4. Check for Unverified Claims requiring Faculty Review
        unverified_count = sum(1 for f in profile.features if f.evidence_type == EvidenceType.UNVERIFIED_CLAIM)
        verified_count = sum(1 for f in profile.features if f.evidence_type == EvidenceType.VERIFIED_MATCH)

        if len(profile.claimed_contributions) > 0 and verified_count == 0:
            limitations.append("Project author claims distinctive contributions, but code implementation evidence was not detected.")
            return CATEGORY_FACULTY_REVIEW, scores, limitations

        if unverified_count >= 3 and verified_count < 2:
            limitations.append("Multiple documented features lack matching source code implementation files.")
            return CATEGORY_FACULTY_REVIEW, scores, limitations

        # 5. Categorize based on cohort similarity and distinctiveness
        if max_overall_sim >= 0.70:
            limitations.append(
                f"Substantial overlap detected with peer submission (similarity {round(max_overall_sim * 100, 1)}%)."
            )
            return CATEGORY_LIMITED_DIFFERENTIATION, scores, limitations

        if (problem_dist >= 0.60 or solution_dist >= 0.60) and feature_diff >= 0.50 and tech_contrib >= 0.60 and evidence_quality >= 0.50:
            return CATEGORY_STRONG_DISTINCTIVE, scores, limitations

        if max_overall_sim < 0.60:
            return CATEGORY_SOME_DISTINCTIVE, scores, limitations

        return CATEGORY_LIMITED_DIFFERENTIATION, scores, limitations

    @classmethod
    def _calculate_technical_contribution(cls, profile: ProjectProfile) -> float:
        """Score technical implementation complexity based on architecture, algorithms, and modules."""
        score = 0.2  # baseline
        if profile.algorithms:
            score += min(0.3, len(profile.algorithms) * 0.15)
        if profile.databases:
            score += 0.15
        if len(profile.modules) >= 3:
            score += 0.2
        if len(profile.backend_components) >= 3:
            score += 0.15
        return round(min(1.0, score), 4)

    @classmethod
    def _calculate_evidence_quality(cls, profile: ProjectProfile) -> float:
        """Score proportion of features backed by verified implementation evidence."""
        if not profile.features:
            return 0.3 if profile.has_documentation else 0.1
        verified = sum(1 for f in profile.features if f.evidence_type == EvidenceType.VERIFIED_MATCH)
        detected = sum(1 for f in profile.features if f.evidence_type == EvidenceType.DETECTED_IMPLEMENTATION)
        total = len(profile.features)
        ratio = (verified + (0.5 * detected)) / total
        return round(min(1.0, max(0.0, ratio)), 4)

    @staticmethod
    def _empty_scores() -> Dict[str, float]:
        return {
            "problem_distinctiveness": 0.0,
            "solution_distinctiveness": 0.0,
            "feature_differentiation": 0.0,
            "technical_contribution": 0.0,
            "evidence_supporting_claim": 0.0,
            "max_cohort_similarity": 0.0,
            "average_cohort_similarity": 0.0,
        }

