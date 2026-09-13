import re
from typing import Dict, Any, List

KNOWN_TECH_CLAIMS = [
    "XGBoost", "RandomForest", "Flask", "Django", "FastAPI",
    "React", "Next.js", "PostgreSQL", "SQLite", "MongoDB",
    "PyTorch", "TensorFlow", "Scikit-Learn", "Docker", "CUDA"
]

def analyze_code_doc_consistency(
    doc_text: str,
    detected_technologies: List[Dict[str, Any]],
    source_files_content: str
) -> Dict[str, Any]:
    """
    Extracts claims from documentation and compares them against actual detected technologies in code.
    Generates IMPLEMENTATION_MISMATCH findings when documented claim is absent from code.
    """
    if not doc_text:
        return {"mismatches": [], "matched_claims": [], "consistency_score": 100.0}

    detected_names = {t.get("name", "").lower() for t in detected_technologies}
    code_text_lower = source_files_content.lower()

    mismatches = []
    matched_claims = []

    for tech in KNOWN_TECH_CLAIMS:
        pattern = re.compile(rf'\b{re.escape(tech)}\b', re.IGNORECASE)
        if pattern.search(doc_text):
            # Claim exists in documentation
            tech_lower = tech.lower()
            is_present = (tech_lower in detected_names) or (tech_lower in code_text_lower)

            if is_present:
                matched_claims.append({
                    "claim": tech,
                    "status": "VERIFIED",
                    "evidence": f"Found matching implementation signatures for {tech} in codebase."
                })
            else:
                mismatches.append({
                    "type": "IMPLEMENTATION_MISMATCH",
                    "severity": "HIGH",
                    "claim": tech,
                    "message": f"Documentation claims usage of {tech}, but no matching code imports or framework files were detected.",
                    "recommendation": f"Ensure {tech} implementation code is committed or correct project report documentation."
                })

    mismatch_penalty = len(mismatches) * 20.0
    consistency_score = max(0.0, min(100.0, round(100.0 - mismatch_penalty, 1)))

    return {
        "mismatches": mismatches,
        "matched_claims": matched_claims,
        "consistency_score": consistency_score,
    }
