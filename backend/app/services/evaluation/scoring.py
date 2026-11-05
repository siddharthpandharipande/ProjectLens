"""Deterministic scoring engine for ProjectLens overall evaluation (Final Phase).

Calculates a transparent, explainable score out of 100 based on weighted
evaluation categories, with dynamic weight renormalization for missing
or unavailable analyses.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.schemas.evaluation import CategoryScoreSchema, ScoreBreakdownItem

# Configurable category weights summing to exactly 100.0%
DEFAULT_CATEGORY_WEIGHTS: Dict[str, float] = {
    "code_quality": 30.0,
    "similarity": 15.0,
    "documentation": 20.0,
    "git_history": 10.0,
    "innovation": 15.0,
    "engineering_readiness": 10.0,
}

CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "code_quality": "Code Quality & Maintainability",
    "similarity": "Originality & Similarity Screening",
    "documentation": "Documentation & Claim Verification",
    "git_history": "Development History & Version Control",
    "innovation": "Innovation & Technical Contribution",
    "engineering_readiness": "Engineering Rigor & Viva Readiness",
}

# Coverage thresholds
COMPLETE_COVERAGE_THRESHOLD = 70.0
MINIMUM_EVALUATION_COVERAGE_THRESHOLD = 50.0


def compute_grade(score: Optional[float]) -> Optional[str]:
    """Map numeric score (0-100) to academic letter grade."""
    if score is None:
        return None
    if score >= 85.0:
        return "A"
    if score >= 75.0:
        return "B+"
    if score >= 65.0:
        return "B"
    if score >= 50.0:
        return "C"
    if score >= 35.0:
        return "D"
    return "F"


class EvaluationScoringEngine:
    """Consolidates category scores and computes overall weighted evaluation."""

    @classmethod
    def calculate_overall_evaluation(
        cls,
        category_scores: List[CategoryScoreSchema],
        weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[Optional[float], Optional[str], str, float, List[CategoryScoreSchema], List[ScoreBreakdownItem]]:
        """Compute overall evaluation score, grade, status, coverage, and contributions.

        Returns:
            (overall_score, grade, evaluation_status, coverage_pct, updated_category_scores, score_breakdown)
        """
        active_weights = weights or DEFAULT_CATEGORY_WEIGHTS
        total_configured_weight = sum(active_weights.values())
        if abs(total_configured_weight - 100.0) > 0.01:
            raise ValueError(f"Category weights must sum to exactly 100.0%, got {total_configured_weight}%")

        assessed_weight = 0.0
        weighted_sum = 0.0
        updated_categories: List[CategoryScoreSchema] = []
        score_breakdown: List[ScoreBreakdownItem] = []

        for cat in category_scores:
            weight = active_weights.get(cat.id, cat.weight)
            updated_cat = cat.model_copy()
            updated_cat.weight = weight

            if cat.status == "assessed" and cat.score is not None:
                # Clamp score to [0.0, 100.0]
                clamped_score = max(0.0, min(100.0, float(cat.score)))
                contribution = round(clamped_score * (weight / 100.0), 2)
                updated_cat.score = round(clamped_score, 1)
                updated_cat.contribution = contribution
                
                assessed_weight += weight
                weighted_sum += (clamped_score * weight)
                
                score_breakdown.append(
                    ScoreBreakdownItem(
                        dimension=updated_cat.name,
                        score=round(clamped_score, 1),
                        maxScore=100.0,
                        notes=f"Weight: {weight}% | Contributed: {contribution} pts",
                    )
                )
            else:
                updated_cat.contribution = 0.0
                score_breakdown.append(
                    ScoreBreakdownItem(
                        dimension=updated_cat.name,
                        score=0.0,
                        maxScore=100.0,
                        notes=f"Weight: {weight}% | Status: {updated_cat.status} ({updated_cat.reason or 'Unassessed'})",
                    )
                )

            updated_categories.append(updated_cat)

        coverage_pct = round(assessed_weight, 1)

        # Determine evaluation status and overall score
        if assessed_weight < MINIMUM_EVALUATION_COVERAGE_THRESHOLD:
            # Below 50% assessed weight: cannot certify valid score
            overall_score = None
            grade = None
            evaluation_status = "incomplete"
        elif assessed_weight < COMPLETE_COVERAGE_THRESHOLD:
            # 50% to 69% assessed weight: provisional partial evaluation
            # Renormalize weighted sum across assessed weight
            overall_score = round(weighted_sum / assessed_weight, 1)
            grade = compute_grade(overall_score)
            evaluation_status = "partial"
        else:
            # >= 70% assessed weight: complete evaluation
            # Renormalize across assessed weight to avoid unfair penalties for missing non-essential data
            overall_score = round(weighted_sum / assessed_weight, 1)
            grade = compute_grade(overall_score)
            evaluation_status = "complete"

        return overall_score, grade, evaluation_status, coverage_pct, updated_categories, score_breakdown

