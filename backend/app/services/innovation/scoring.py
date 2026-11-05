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

# Transparent Confidence Classifications (Section 4.D)
CONFIDENCE_DIRECTLY_VERIFIED = "Directly Verified"
CONFIDENCE_STRONG_EVIDENCE = "Strong Evidence"
CONFIDENCE_MODERATE_EVIDENCE = "Moderate Evidence"
CONFIDENCE_INDIRECT_EVIDENCE = "Indirect Evidence"
CONFIDENCE_UNVERIFIED = "Unverified"
CONFIDENCE_INSUFFICIENT_EVIDENCE = "Insufficient Evidence"


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
                "problem_distinctiveness": None,
                "solution_distinctiveness": None,
                "feature_differentiation": None,
                "technical_contribution": cls._calculate_technical_contribution(profile),
                "evidence_supporting_claim": cls._calculate_evidence_quality(profile),
                "max_cohort_similarity": None,
                "average_cohort_similarity": None,
                "confidence_classification": CONFIDENCE_INSUFFICIENT_EVIDENCE,
                "confidence_rationale": "No comparable cohort submissions available to establish relative distinctiveness.",
            }
            return CATEGORY_INSUFFICIENT_EVIDENCE, scores, limitations

        # 3. Calculate dimension-wise similarity and distinctiveness
        max_overall_sim = max((m.get("overall_similarity", 0.0) for m in matches), default=0.0)
        avg_overall_sim = sum(m.get("overall_similarity", 0.0) for m in matches) / max(1, len(matches))

        max_problem_sim = max((m.get("problem_similarity", 0.0) for m in matches), default=0.0)
        max_solution_sim = max((m.get("solution_similarity", 0.0) for m in matches), default=0.0)
        max_feature_sim = max((m.get("feature_similarity", 0.0) for m in matches), default=0.0)

        # Audit: verify whether extracted texts are genuine or generic/unidentified
        not_identified_marker = "Not identified from the available project documents."
        has_valid_problem = bool(
            profile.problem_statement
            and profile.problem_statement != not_identified_marker
            and len(profile.problem_statement.strip()) >= 25
        )
        has_valid_solution = bool(
            profile.proposed_solution
            and profile.proposed_solution != not_identified_marker
            and len(profile.proposed_solution.strip()) >= 25
        )
        has_features = len(profile.features) > 0

        # When evidence is missing or generic, do not falsely award 100% distinctiveness (1.0 - 0.0). Mark as None (Insufficient Evidence).
        problem_dist = round(max(0.0, min(1.0, 1.0 - max_problem_sim)), 4) if has_valid_problem else None
        solution_dist = round(max(0.0, min(1.0, 1.0 - max_solution_sim)), 4) if has_valid_solution else None
        feature_diff = round(max(0.0, min(1.0, 1.0 - max_feature_sim)), 4) if has_features else None

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
        detected_count = sum(1 for f in profile.features if f.evidence_type == EvidenceType.DETECTED_IMPLEMENTATION)

        # Compute transparent confidence classification (Section 4.D)
        if not has_features and not profile.has_documentation:
            conf_class = CONFIDENCE_INSUFFICIENT_EVIDENCE
            conf_rationale = "Project documentation and features are absent; insufficient evidence for novelty classification."
        elif unverified_count >= 2 and verified_count == 0:
            conf_class = CONFIDENCE_UNVERIFIED
            conf_rationale = f"{unverified_count} feature claims documented without matching source code implementations."
        elif verified_count >= 2 and (evidence_quality or 0) >= 0.70 and max_overall_sim < 0.60:
            conf_class = CONFIDENCE_DIRECTLY_VERIFIED
            conf_rationale = f"{verified_count} features verified directly in source code AST with low cohort overlap ({round(max_overall_sim * 100, 1)}%)."
        elif verified_count >= 1 and (tech_contrib or 0) >= 0.50:
            conf_class = CONFIDENCE_STRONG_EVIDENCE
            conf_rationale = "Technical implementation is verified in source code with distinctive architecture."
        elif detected_count > 0 and verified_count == 0:
            conf_class = CONFIDENCE_INDIRECT_EVIDENCE
            conf_rationale = "Source code components detected from files, but formal documentation claims are absent."
        elif max_overall_sim >= 0.70:
            conf_class = CONFIDENCE_MODERATE_EVIDENCE
            conf_rationale = f"High similarity ({round(max_overall_sim * 100, 1)}%) with peer submission limits distinctive confidence."
        else:
            conf_class = CONFIDENCE_MODERATE_EVIDENCE
            conf_rationale = "Moderate evidence available across partial code implementations and documentation."

        scores["confidence_classification"] = conf_class
        scores["confidence_rationale"] = conf_rationale

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

        p_dist_val = problem_dist if problem_dist is not None else 0.0
        s_dist_val = solution_dist if solution_dist is not None else 0.0
        f_diff_val = feature_diff if feature_diff is not None else 0.0
        tc_val = tech_contrib if tech_contrib is not None else 0.0
        eq_val = evidence_quality if evidence_quality is not None else 0.0

        if (p_dist_val >= 0.60 or s_dist_val >= 0.60) and f_diff_val >= 0.50 and tc_val >= 0.60 and eq_val >= 0.50:
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
    def _empty_scores() -> Dict[str, Any]:
        return {
            "problem_distinctiveness": None,
            "solution_distinctiveness": None,
            "feature_differentiation": None,
            "technical_contribution": None,
            "evidence_supporting_claim": None,
            "max_cohort_similarity": None,
            "average_cohort_similarity": None,
            "confidence_classification": CONFIDENCE_INSUFFICIENT_EVIDENCE,
            "confidence_rationale": "Project contains insufficient information to assess innovation confidence.",
        }

