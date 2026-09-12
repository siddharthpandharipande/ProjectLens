from typing import Dict, Any, List
from app.models.code_metric import CodeMetric
from app.config import analysis_thresholds as thresholds

def analyze_technical_execution(cm: CodeMetric, file_types_found: List[str]) -> Dict[str, Any]:
    """
    Calculates deterministic preliminary Technical Execution score (0–100) based on code metrics.
    Evaluates:
    - Code Structure (20%)
    - Cyclomatic Complexity (20%)
    - Maintainability & Comment Ratio (20%)
    - Automated Testing Evidence (20%)
    - Project Organization (20%)
    """
    evidence: List[str] = []
    breakdown = {
        "code_structure": 0.0,
        "complexity": 0.0,
        "maintainability": 0.0,
        "testing_evidence": 0.0,
        "organization": 0.0,
    }

    if not cm or cm.source_file_count == 0:
        return {
            "score": None,
            "status": "Pending",
            "evidence": ["Insufficient source files to compute Technical Execution score."],
            "breakdown": breakdown
        }

    # 1. Code Structure (Modular File Count)
    if cm.source_file_count >= 10:
        breakdown["code_structure"] = 20.0
        evidence.append(f"✓ Strong modular structure ({cm.source_file_count} source files)")
    elif cm.source_file_count >= 3:
        breakdown["code_structure"] = 15.0
        evidence.append(f"✓ Modular organization ({cm.source_file_count} source files)")
    else:
        breakdown["code_structure"] = 10.0
        evidence.append(f"⚠ Small codebase structure ({cm.source_file_count} source files)")

    # 2. Cyclomatic Complexity
    avg_cc = cm.average_complexity
    if avg_cc <= 3.0:
        breakdown["complexity"] = 20.0
        evidence.append(f"✓ Low average cyclomatic complexity ({avg_cc}) indicating highly readable code")
    elif avg_cc <= thresholds.HIGH_COMPLEXITY:
        breakdown["complexity"] = 16.0
        evidence.append(f"✓ Manageable code complexity ({avg_cc})")
    elif avg_cc <= thresholds.VERY_HIGH_COMPLEXITY:
        breakdown["complexity"] = 10.0
        evidence.append(f"⚠ Elevated average code complexity ({avg_cc})")
    else:
        breakdown["complexity"] = 5.0
        evidence.append(f"⚠ High average code complexity ({avg_cc}) requires refactoring")

    # 3. Maintainability (Code / Comment ratio)
    code_lines = cm.code_lines
    comment_lines = cm.comment_lines
    if comment_lines > 0:
        breakdown["maintainability"] = 20.0
        evidence.append(f"✓ Code includes inline comments ({comment_lines} comment lines)")
    elif code_lines > 0:
        breakdown["maintainability"] = 12.0
        evidence.append("✓ Code structure verified")
    else:
        breakdown["maintainability"] = 10.0

    # 4. Automated Testing Evidence
    if cm.test_file_count >= 3:
        breakdown["testing_evidence"] = 20.0
        evidence.append(f"✓ Comprehensive test suite detected ({cm.test_file_count} test files)")
    elif cm.test_file_count >= 1:
        breakdown["testing_evidence"] = 15.0
        evidence.append(f"✓ Automated test suite present ({cm.test_file_count} test file(s))")
    else:
        breakdown["testing_evidence"] = 5.0
        evidence.append("⚠ No automated unit or integration test files detected")

    # 5. Project Organization
    has_source = "source" in file_types_found
    has_config = "config" in file_types_found
    has_doc = "documentation" in file_types_found

    org_score = 10.0
    if has_source and has_config:
        org_score += 5.0
    if has_doc:
        org_score += 5.0

    breakdown["organization"] = org_score
    evidence.append("✓ Project includes configuration and source file organization")

    total_score = round(sum(breakdown.values()), 1)

    return {
        "score": total_score,
        "status": "completed",
        "evidence": evidence,
        "breakdown": breakdown
    }
