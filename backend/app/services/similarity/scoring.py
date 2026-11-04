"""
scoring.py

Similarity scoring engine and project-level aggregation service.

Key Principles:
1. Dynamic Weight Re-normalization:
   Provisional defaults: Token 30%, Structure 40%, Semantic 30%.
   If any component is missing or unsupported, active weights re-normalize over available components.
   If no component is available, returns None.

2. Coverage-Aware Project-Level Aggregation:
   Accounts for unmatched comparable source files, source-code coverage, and the proportion
   of each project represented by matched code. A small 10-line matching file in a 1,000-line
   codebase will not distort the overall project similarity signal.

3. Responsible & Non-Accusatory Interpretation:
   Categorizes signals as High, Moderate, Low, or Minimal.
   Explicitly disclaims plagiarism verdicts: "Advisory evidence only. Similarity signals
   do not constitute proof of academic misconduct."
"""

from typing import List, Dict, Any, Optional, Tuple
from app.config import settings


class SimilarityScoringEngine:
    """Calculates file-pair combined scores and aggregated project similarity signals."""

    # Categorization thresholds (configurable)
    CATEGORY_HIGH = 70.0
    CATEGORY_MODERATE = 40.0
    CATEGORY_LOW = 20.0

    # Minimum file-level similarity percentage to be counted as a notable match
    MIN_NOTABLE_MATCH_THRESHOLD = 15.0

    ADVISORY_NOTE = (
        "Advisory evidence only. Similarity signals do not constitute proof of "
        "academic misconduct. High similarity may occur from shared library boilerplate, "
        "assignment templates, or standard algorithmic patterns."
    )

    @classmethod
    def calculate_file_combined_score(
        cls,
        token_sim: Optional[float],
        structural_sim: Optional[float],
        semantic_sim: Optional[float],
    ) -> Tuple[Optional[float], str]:
        """
        Combine available component scores using dynamic weight re-normalization.
        Returns:
            Tuple of (combined_score_float_or_None, method_description_str)
        """
        weights: Dict[str, float] = {}
        scores: Dict[str, float] = {}

        if token_sim is not None:
            weights["token"] = settings.SIMILARITY_WEIGHT_TOKEN
            scores["token"] = token_sim

        if structural_sim is not None:
            weights["structural"] = settings.SIMILARITY_WEIGHT_STRUCTURE
            scores["structural"] = structural_sim

        if semantic_sim is not None:
            weights["semantic"] = settings.SIMILARITY_WEIGHT_SEMANTIC
            scores["semantic"] = semantic_sim

        if not weights:
            return None, "insufficient_evidence"

        total_weight = sum(weights.values())
        if total_weight <= 0:
            return None, "insufficient_evidence"

        combined = sum(scores[k] * (weights[k] / total_weight) for k in weights)
        method_desc = "+".join(sorted(weights.keys()))
        return round(combined, 1), method_desc

    @classmethod
    def get_similarity_category(cls, score: float) -> str:
        """Map score to responsible review signal tier."""
        if score >= cls.CATEGORY_HIGH:
            return "high"
        elif score >= cls.CATEGORY_MODERATE:
            return "moderate"
        elif score >= cls.CATEGORY_LOW:
            return "low"
        return "minimal"

    @classmethod
    def aggregate_project_similarity(
        cls,
        current_project_sloc: int,
        matched_project_sloc: int,
        file_matches: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregates file-pair matches into a coverage-aware project-level similarity signal.
        
        Formula:
        - WeightedMatchSum = sum(combined_score * min(sloc_a, sloc_b)) for all notable file pairs
        - Denominator = max(1, (current_project_sloc + matched_project_sloc) / 2)
        - OverallProjectSimilarity = min(100.0, WeightedMatchSum / Denominator)
        - Source coverage = sum(sloc_a for matched files) / total current_project_sloc
        - Matched coverage = sum(sloc_b for matched files) / total matched_project_sloc
        """
        if not file_matches or (current_project_sloc <= 0 and matched_project_sloc <= 0):
            return {
                "overall_similarity": 0.0,
                "similarity_category": "minimal",
                "token_similarity": None,
                "structural_similarity": None,
                "semantic_similarity": None,
                "source_coverage_pct": 0.0,
                "matched_coverage_pct": 0.0,
                "identical_statements_count": 0,
                "matched_files_count": 0,
            }

        # Filter notable matches
        notable_matches = [
            m for m in file_matches if (m.get("similarityPercent") or 0.0) >= cls.MIN_NOTABLE_MATCH_THRESHOLD
        ]

        if not notable_matches:
            return {
                "overall_similarity": 0.0,
                "similarity_category": "minimal",
                "token_similarity": None,
                "structural_similarity": None,
                "semantic_similarity": None,
                "source_coverage_pct": 0.0,
                "matched_coverage_pct": 0.0,
                "identical_statements_count": 0,
                "matched_files_count": 0,
            }

        weighted_match_sum = 0.0
        token_sum = 0.0
        struct_sum = 0.0
        semantic_sum = 0.0
        token_weight_sum = 0.0
        struct_weight_sum = 0.0
        semantic_weight_sum = 0.0

        matched_sloc_current = 0
        matched_sloc_matched = 0
        total_identical_statements = 0

        for m in notable_matches:
            score = m.get("similarityPercent") or 0.0
            sloc_a = m.get("currentSloc") or 10
            sloc_b = m.get("matchedSloc") or 10
            effective_weight = min(sloc_a, sloc_b)

            weighted_match_sum += score * effective_weight
            matched_sloc_current += sloc_a
            matched_sloc_matched += sloc_b
            total_identical_statements += m.get("identicalStatements") or 0

            if m.get("tokenSimilarity") is not None:
                token_sum += m["tokenSimilarity"] * effective_weight
                token_weight_sum += effective_weight

            if m.get("structuralSimilarity") is not None:
                struct_sum += m["structuralSimilarity"] * effective_weight
                struct_weight_sum += effective_weight

            if m.get("semanticSimilarity") is not None:
                semantic_sum += m["semanticSimilarity"] * effective_weight
                semantic_weight_sum += effective_weight

        # Effective denominator accounts for full project size
        cur_sloc = max(current_project_sloc, 1)
        mat_sloc = max(matched_project_sloc, 1)
        denominator = (cur_sloc + mat_sloc) / 2.0

        overall_similarity = min(100.0, round(weighted_match_sum / denominator, 1))
        source_coverage_pct = min(100.0, round((matched_sloc_current / cur_sloc) * 100.0, 1))
        matched_coverage_pct = min(100.0, round((matched_sloc_matched / mat_sloc) * 100.0, 1))

        avg_token = round(token_sum / token_weight_sum, 1) if token_weight_sum > 0 else None
        avg_struct = round(struct_sum / struct_weight_sum, 1) if struct_weight_sum > 0 else None
        avg_semantic = round(semantic_sum / semantic_weight_sum, 1) if semantic_weight_sum > 0 else None

        return {
            "overall_similarity": overall_similarity,
            "similarity_category": cls.get_similarity_category(overall_similarity),
            "token_similarity": avg_token,
            "structural_similarity": avg_struct,
            "semantic_similarity": avg_semantic,
            "source_coverage_pct": source_coverage_pct,
            "matched_coverage_pct": matched_coverage_pct,
            "identical_statements_count": total_identical_statements,
            "matched_files_count": len(notable_matches),
        }
