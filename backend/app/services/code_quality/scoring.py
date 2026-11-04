"""
scoring.py

Transparent, deterministic Code Quality scoring engine.
Produces a reproducible preliminary code-quality score (0-100) and an
audit-ready score explanation.

Distinguished from the final ProjectLens evaluation score:
This module does NOT calculate an overall project grade.
"""

from typing import List, Dict, Any, Tuple, Optional


class DeterministicQualityScorer:
    """
    Deterministic scoring model based on weighted code quality factors.
    Thresholds and factor weights are explicit and configurable.
    """

    # Base factor weights (sum = 100.0)
    DEFAULT_WEIGHT_SYNTAX: float = 25.0
    DEFAULT_WEIGHT_COMPLEXITY: float = 35.0
    DEFAULT_WEIGHT_STRUCTURE: float = 20.0
    DEFAULT_WEIGHT_HYGIENE: float = 20.0

    @classmethod
    def calculate_score(
        cls,
        file_metrics: List[Dict[str, Any]],
        project_metrics: Dict[str, Any],
        findings: List[Dict[str, Any]],
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """
        Calculate deterministic code-quality score and return:
          (score: Optional[float], explanation: Dict[str, Any])

        If evidence is insufficient (e.g. 0 source files), returns:
          (None, explanation) without inventing numbers.
        """
        total_source_files = len(file_metrics)
        if total_source_files == 0:
            return None, {
                "factors": [],
                "strengths": [],
                "deductions": ["No source code files were found or eligible for analysis."],
                "summary": "Insufficient source code evidence to calculate a defensible code quality score.",
            }

        # Check which metrics are available across files
        has_radon = any(f.get("maintainability_index") is not None for f in file_metrics)
        has_syntax_data = True
        has_structure_data = True
        has_hygiene_data = True

        factors: List[Dict[str, Any]] = []
        strengths: List[str] = []
        deductions: List[str] = []

        # ─── Factor 1: Syntax & Parser Integrity (Max 25 pts) ─────────────────
        weight_syntax = cls.DEFAULT_WEIGHT_SYNTAX
        syntax_errors = sum(1 for f in file_metrics if f.get("has_syntax_error"))
        if syntax_errors == 0:
            syntax_score = weight_syntax
            strengths.append(f"100% of analyzed source files ({total_source_files}) parsed cleanly without syntax errors.")
            syntax_notes = "All source files parsed without syntax or AST errors."
        else:
            fraction_broken = min(syntax_errors / total_source_files, 1.0)
            syntax_deduction = fraction_broken * weight_syntax
            syntax_score = max(weight_syntax - syntax_deduction, 0.0)
            deductions.append(f"{syntax_errors} file(s) contain syntax/compilation errors (-{syntax_deduction:.1f} pts).")
            syntax_notes = f"{syntax_errors} / {total_source_files} file(s) contain syntax errors."

        factors.append({
            "name": "Syntax & Parser Integrity",
            "weight": weight_syntax,
            "score": round(syntax_score, 1),
            "maxScore": weight_syntax,
            "notes": syntax_notes,
        })

        # ─── Factor 2: Complexity & Maintainability (Max 35 pts) ──────────────
        # Only active when Radon / complexity calculations are supported
        if has_radon:
            weight_complexity = cls.DEFAULT_WEIGHT_COMPLEXITY
            comp_score = weight_complexity

            avg_cc = project_metrics.get("avg_complexity")
            max_cc = project_metrics.get("max_complexity")
            avg_mi = project_metrics.get("avg_maintainability_index")

            # Average cyclomatic complexity evaluation
            if avg_cc is not None:
                if avg_cc <= 5.0:
                    strengths.append(f"Low average cyclomatic complexity ({avg_cc:.1f} per block).")
                elif avg_cc <= 10.0:
                    comp_score -= 4.0
                    deductions.append(f"Moderate average cyclomatic complexity ({avg_cc:.1f} per block, -4.0 pts).")
                elif avg_cc <= 15.0:
                    comp_score -= 10.0
                    deductions.append(f"High average cyclomatic complexity ({avg_cc:.1f} per block, -10.0 pts).")
                else:
                    comp_score -= 18.0
                    deductions.append(f"Very high average cyclomatic complexity ({avg_cc:.1f} per block, -18.0 pts).")

            # Critical complexity blocks (CC > 15)
            critical_blocks = sum(
                1 for f in file_metrics
                for b in (f.get("complexity_blocks") or [])
                if b.get("complexity", 0) > 15
            )
            if critical_blocks > 0:
                crit_deduction = min(critical_blocks * 3.0, 10.0)
                comp_score -= crit_deduction
                deductions.append(f"{critical_blocks} critical function(s) with CC > 15 (-{crit_deduction:.1f} pts).")

            # Maintainability Index evaluation (0-100)
            if avg_mi is not None:
                if avg_mi >= 65.0:
                    strengths.append(f"Strong maintainability index ({avg_mi:.1f} / 100, Radon Rank A).")
                elif avg_mi >= 40.0:
                    comp_score -= 4.0
                    deductions.append(f"Moderate maintainability index ({avg_mi:.1f} / 100, -4.0 pts).")
                elif avg_mi >= 20.0:
                    comp_score -= 8.0
                    deductions.append(f"Low maintainability index ({avg_mi:.1f} / 100, -8.0 pts).")
                else:
                    comp_score -= 12.0
                    deductions.append(f"Critically low maintainability index ({avg_mi:.1f} / 100, -12.0 pts).")

            comp_score = max(comp_score, 0.0)
            factors.append({
                "name": "Complexity & Maintainability (Radon)",
                "weight": weight_complexity,
                "score": round(comp_score, 1),
                "maxScore": weight_complexity,
                "notes": f"Avg CC: {avg_cc or 'N/A'}, Max CC: {max_cc or 'N/A'}, Avg MI: {avg_mi or 'N/A'}.",
            })
        else:
            weight_complexity = 0.0

        # ─── Factor 3: Code Structure & Nesting (Max 20 pts) ───────────────────
        weight_structure = cls.DEFAULT_WEIGHT_STRUCTURE
        struct_score = weight_structure

        # Long functions (>50 SLOC) and very long (>100 SLOC)
        long_fns = 0
        very_long_fns = 0
        deep_nesting_count = 0

        for f in file_metrics:
            for fn in (f.get("functions_metadata") or []):
                sloc = fn.get("sloc", 0)
                if sloc > 100:
                    very_long_fns += 1
                elif sloc > 50:
                    long_fns += 1

            nesting = f.get("max_nesting_depth")
            if nesting is not None and nesting > 4:
                deep_nesting_count += 1

        if long_fns > 0 or very_long_fns > 0:
            fn_deduction = min((long_fns * 1.5) + (very_long_fns * 3.0), 8.0)
            struct_score -= fn_deduction
            deductions.append(f"{long_fns + very_long_fns} oversized function(s) detected (-{fn_deduction:.1f} pts).")
        else:
            strengths.append("Modular function sizing; no oversized functions detected.")

        if deep_nesting_count > 0:
            nest_deduction = min(deep_nesting_count * 2.5, 8.0)
            struct_score -= nest_deduction
            deductions.append(f"{deep_nesting_count} file(s) with deep control flow nesting > 4 (-{nest_deduction:.1f} pts).")
        else:
            strengths.append("Well-structured control flow without excessive nesting depth.")

        struct_score = max(struct_score, 0.0)
        factors.append({
            "name": "Code Structure & Modularity",
            "weight": weight_structure,
            "score": round(struct_score, 1),
            "maxScore": weight_structure,
            "notes": f"{long_fns + very_long_fns} oversized functions, {deep_nesting_count} deeply nested files.",
        })

        # ─── Factor 4: Code Hygiene & Documentation (Max 20 pts) ──────────────
        weight_hygiene = cls.DEFAULT_WEIGHT_HYGIENE
        hygiene_score = weight_hygiene

        total_sloc = project_metrics.get("total_sloc", 0)
        total_comments = project_metrics.get("total_comments", 0)

        # Comment density ratio
        comment_ratio = total_comments / max(total_sloc, 1)
        if comment_ratio >= 0.10:
            strengths.append(f"Healthy inline commenting density ({comment_ratio * 100:.1f}% comments to SLOC).")
        elif comment_ratio >= 0.04:
            hygiene_score -= 3.0
            deductions.append(f"Low inline comment density ({comment_ratio * 100:.1f}%, -3.0 pts).")
        else:
            hygiene_score -= 6.0
            deductions.append(f"Sparse commenting across codebase ({comment_ratio * 100:.1f}%, -6.0 pts).")

        # Missing docstrings on substantial functions
        missing_docstrings = sum(
            1 for f in file_metrics
            for fn in (f.get("functions_metadata") or [])
            if not fn.get("has_docstring") and fn.get("sloc", 0) >= 15
        )
        if missing_docstrings > 0:
            doc_deduction = min(missing_docstrings * 1.5, 8.0)
            hygiene_score -= doc_deduction
            deductions.append(f"{missing_docstrings} substantial function(s) lack docstrings (-{doc_deduction:.1f} pts).")
        else:
            strengths.append("Functions and classes have docstrings where applicable.")

        hygiene_score = max(hygiene_score, 0.0)
        factors.append({
            "name": "Documentation & Code Hygiene",
            "weight": weight_hygiene,
            "score": round(hygiene_score, 1),
            "maxScore": weight_hygiene,
            "notes": f"Comment ratio: {comment_ratio * 100:.1f}%, {missing_docstrings} missing docstrings.",
        })

        # ─── Final Normalization ──────────────────────────────────────────────
        total_active_weight = sum(f["weight"] for f in factors)
        total_earned_score = sum(f["score"] for f in factors)

        if total_active_weight > 0:
            normalized_score = round((total_earned_score / total_active_weight) * 100.0, 1)
        else:
            normalized_score = None

        if normalized_score is not None:
            normalized_score = max(0.0, min(100.0, normalized_score))
            summary = (
                f"Preliminary code quality score of {normalized_score}/100 calculated across "
                f"{total_source_files} source files and {len(factors)} active metric dimensions."
            )
        else:
            summary = "Insufficient metric dimensions active to calculate score."

        explanation = {
            "factors": factors,
            "strengths": strengths,
            "deductions": deductions,
            "summary": summary,
        }

        return normalized_score, explanation
