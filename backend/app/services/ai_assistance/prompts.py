"""Prompt construction for the AI-Assistance Analyzer (Phase 7A).

Contains the system prompt given to the LLM and a renderer that turns the
deterministic evidence summary into a compact, PII-free user prompt. No source
code, personal identifiers, secrets, or full documents are ever included.
"""

from app.services.llm.schemas import EvidenceSummary

SYSTEM_PROMPT = (
    "You are a careful academic-integrity assistant for a faculty project "
    "evaluation system called ProjectLens. You receive a compact, structured "
    "evidence summary collected by deterministic Python analysis (NOT source "
    "code, NOT personal identifiers, NOT secrets). Your job is to interpret "
    "the evidence and return a structured JSON object.\n\n"
    "STRICT RULES:\n"
    "1. Return ONLY valid JSON matching the requested schema. No markdown, no "
    "extra prose, no code fences.\n"
    "2. Every evidence reference you emit MUST use a signal_id that appears in "
    "the input evidence summary. Do not invent or reference signal IDs that "
    "were not supplied.\n"
    "3. Do not create metrics, commits, matching files, or analysis findings "
    "that were not in the input.\n"
    "4. Do not output an AI-use probability percentage. Do not claim the "
    "student definitely used AI, that the project is AI-generated, or that the "
    "student committed misconduct.\n"
    "5. Clearly separate directly observed facts from interpretation and "
    "speculation.\n"
    "6. Include alternative explanations and limitations.\n"
    "7. Keep all strings concise. Omit any field you cannot support."
)


def build_user_prompt(evidence: EvidenceSummary) -> str:
    """Render the evidence summary as a compact text prompt for the LLM."""
    lines: list[str] = []
    lines.append(f"Project ID: {evidence.project_id}")
    lines.append(f"Rules version: {evidence.rules_version}")
    if evidence.advisory_category:
        lines.append(f"Advisory category: {evidence.advisory_category}")
    lines.append("")
    lines.append("Evidence signals (deterministic, collected by Python):")
    if not evidence.signals:
        lines.append("  (none available)")
    for sig in evidence.signals:
        lines.append(
            f"  - id={sig.signal_id} | category={sig.category} | "
            f"source={sig.source} | availability={sig.availability_status}"
        )
        lines.append(f"      observed: {sig.observed_value}")
        lines.append(f"      explanation: {sig.explanation}")
        if sig.confidence is not None:
            lines.append(f"      confidence: {sig.confidence}")
        if sig.alternative_explanations:
            lines.append(f"      alternative explanations: {'; '.join(sig.alternative_explanations)}")
    lines.append("")
    lines.append(
        "TASK: Interpret the signals above. Return a JSON object with keys: "
        "interpretation_status, executive_summary, explanation_of_patterns, "
        "evidence_references (list of {signal_id, observation}), "
        "alternative_explanations, faculty_follow_up_recommendations, "
        "limitations, fact_vs_interpretation ({facts, interpretation, speculation})."
    )
    return "\n".join(lines)