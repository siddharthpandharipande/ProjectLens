import re
from typing import Dict, Any

REQUIRED_SECTIONS = [
    "abstract",
    "introduction",
    "problem statement",
    "objectives",
    "methodology",
    "system architecture",
    "implementation",
    "results",
    "conclusion",
    "references",
]

def analyze_documentation_structure(text: str) -> Dict[str, Any]:
    """
    Analyzes documentation text to detect standard academic project report sections.
    """
    if not text:
        return {
            "sections_detected": {},
            "coverage_percentage": 0.0,
            "detected_count": 0,
            "total_count": len(REQUIRED_SECTIONS)
        }

    lowered = text.lower()
    sections_detected = {}
    detected_count = 0

    for sec in REQUIRED_SECTIONS:
        # Match heading presence using pattern
        pattern = re.compile(rf'\b{re.escape(sec)}\b', re.IGNORECASE)
        found = bool(pattern.search(lowered))
        sections_detected[sec] = found
        if found:
            detected_count += 1

    coverage_pct = round((detected_count / len(REQUIRED_SECTIONS)) * 100, 1)

    return {
        "sections_detected": sections_detected,
        "coverage_percentage": coverage_pct,
        "detected_count": detected_count,
        "total_count": len(REQUIRED_SECTIONS),
    }
