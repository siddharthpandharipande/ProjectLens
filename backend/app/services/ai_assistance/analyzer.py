"""Deterministic advisory assessment for Phase 7A AI-Assistance Analyzer.

Categorises observable evidence patterns into advisory categories. These are
advisory signals for faculty review — NOT AI-detection probabilities and NOT
proof of misconduct. All logic is transparent, deterministic, and testable.
"""

from typing import Any, Dict, List, Tuple

# Advisory categories in increasing level of concern.
INSUFFICIENT_EVIDENCE = "Insufficient Evidence"
FEW_SIGNALS = "Few Observable Signals"
SOME_SIGNALS = "Some Observable Signals"
MULTIPLE_SIGNALS = "Multiple Observable Signals Requiring Faculty Review"

# Thresholds on the count of *available* evidence signals.
_THRESHOLD_FEW = 3
_THRESHOLD_SOME = 7


class AdvisoryAnalyzer:
    """Deterministic evidence-pattern categorisation."""

    @classmethod
    def assess(
        cls, signals: List[Dict[str, Any]]
    ) -> Tuple[str, str, List[str]]:
        """Categorise the observable evidence signals.

        Returns:
            (advisory_category, reasoning, alternative_explanations)
        """
        available = [
            s for s in signals if s.get("availability_status") == "available"
        ]
        unavailable = [
            s for s in signals if s.get("availability_status") != "available"
        ]
        available_count = len(available)

        # Count high-severity code-quality findings as escalating factors.
        high_findings = [
            s
            for s in available
            if s.get("category") == "code_quality_finding"
        ]

        # Build alternative explanations that apply broadly.
        alternative_explanations: List[str] = [
            "Observed patterns are not independently proof of AI usage or academic misconduct.",
            "Similar code may reflect common educational templates, starter code, or standard algorithms.",
            "A small commit count may result from squashed commits or a single ZIP upload.",
            "Documentation/code mismatches may result from outdated project reports.",
            "Commit timestamps and authorship metadata can be altered by the committer.",
        ]

        if available_count == 0:
            category = INSUFFICIENT_EVIDENCE
            reasoning = (
                "No prior analysis results are available for this project. "
                "There is insufficient evidence to form an advisory assessment. "
                "Run code quality, similarity, documentation, and/or Git history "
                "analysis first, then re-run AI-assistance analysis."
            )
            return category, reasoning, alternative_explanations

        if available_count <= _THRESHOLD_FEW:
            category = FEW_SIGNALS
            reasoning = (
                f"{available_count} observable evidence signal(s) are available. "
                "This provides a limited basis for interpretation. Results should be "
                "treated as preliminary and reviewed alongside other assessment evidence."
            )
            return category, reasoning, alternative_explanations

        if available_count <= _THRESHOLD_SOME:
            category = SOME_SIGNALS
            reasoning = (
                f"{available_count} observable evidence signal(s) are available. "
                "Several patterns are present that merit faculty review, but no single "
                "signal is conclusive. Consider the context of the assignment and course."
            )
            return category, reasoning, alternative_explanations

    # Multiple signals (>= 8) or any high-severity finding escalates review.
        category = MULTIPLE_SIGNALS
        escalation = ""
        if high_findings:
            escalation = (
                f" In addition, {len(high_findings)} high-severity code-quality "
                "finding(s) were detected."
            )
        reasoning = (
            f"{available_count} observable evidence signal(s) are available, "
            "indicating multiple patterns requiring faculty review.{escalation}"
        ).format(escalation=escalation)
        return category, reasoning, alternative_explanations

    @classmethod
    def summary_counts(cls, signals: List[Dict[str, Any]]) -> Dict[str, int]:
        """Return a count of signals grouped by availability status."""
        counts: Dict[str, int] = {}
        for s in signals:
            status = s.get("availability_status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts