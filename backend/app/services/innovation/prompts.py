"""Prompt construction and validation for Phase 7B Innovation Analyzer.

Defines the user prompt builder for Google Gemma 4 26B Free via OpenRouter.
Strips personal identifiers, enforces compact inputs, and validates grounded
evidence references.
"""

from typing import Any, Dict, List
from app.services.innovation.profile import ProjectProfile
from app.services.llm.schemas import (
    InnovationEvidenceReference as EvidenceReference,
    LLMInnovationInterpretation,
)
from app.services.llm.client import INNOVATION_SYSTEM_PROMPT

__all__ = [
    "EvidenceReference",
    "LLMInnovationInterpretation",
    "INNOVATION_SYSTEM_PROMPT",
    "build_innovation_user_prompt",
]


def build_innovation_user_prompt(
    profile: ProjectProfile,
    cohort_size: int,
    matches: List[Dict[str, Any]],
    dimension_scores: Dict[str, Any],
) -> str:
    """Build a compact, PII-free prompt for the LLM."""
    lines: List[str] = []
    lines.append(f"Project ID: {profile.project_id}")
    lines.append(f"Project Title: {profile.title}")
    lines.append(f"Domain: {profile.domain}")
    clean_users = [str(u).strip() for u in (profile.target_users or []) if u and str(u).strip()]
    lines.append(f"Target Users: {', '.join(clean_users) if clean_users else 'General Users'}")
    lines.append("")
    lines.append(f"Problem Statement:\n{profile.problem_statement or '(Not explicitly documented)'}")
    lines.append("")
    lines.append(f"Proposed Solution:\n{profile.proposed_solution or '(Not explicitly documented)'}")
    lines.append("")
    lines.append("Features & Implementation Evidence:")
    if not profile.features:
        lines.append("  (No features extracted)")
    for idx, feat in enumerate(profile.features, start=1):
        lines.append(
            f"  - id=FEAT-{idx} | name={feat.name} | evidence_type={feat.evidence_type}"
        )
        if feat.code_reference:
            lines.append(f"      code_ref: {feat.code_reference}")
        if feat.doc_reference:
            lines.append(f"      doc_ref: {feat.doc_reference}")

    lines.append("")
    tech = (profile.languages or []) + (profile.frameworks or []) + (profile.databases or [])
    clean_tech = [str(t).strip() for t in tech if t and str(t).strip()]
    clean_algo = [str(a).strip() for a in (profile.algorithms or []) if a and str(a).strip()]
    lines.append(f"Technologies: {', '.join(clean_tech) if clean_tech else 'None detected'}")
    lines.append(f"Algorithms: {', '.join(clean_algo) if clean_algo else 'None detected'}")
    lines.append("")
    lines.append(f"Cohort Submissions Evaluated: {cohort_size}")
    if matches:
        top_matches = matches[:3]
        lines.append("Top Peer Comparisons in Cohort:")
        for m in top_matches:
            lines.append(
                f"  * Compared Project: {m.get('compared_project_title')} | Overall Similarity: {m.get('overall_similarity')}"
            )
            lines.append(f"      Differences: {m.get('difference_summary')}")
    else:
        lines.append("Cohort Comparison: No other comparable project submissions exist in the database.")

    lines.append("")
    lines.append(
        "TASK: Provide structured academic assessment in JSON with keys: "
        "interpretation_status, innovation_summary, problem_understanding, "
        "proposed_solution_understanding, potential_contributions (list), "
        "distinctive_elements (list), cohort_comparison_interpretation, "
        "evidence_references (list of {evidence_id, observation}), "
        "alternative_explanations (list), faculty_follow_up_recommendations (list), "
        "limitations (list)."
    )
    return "\n".join(lines)
