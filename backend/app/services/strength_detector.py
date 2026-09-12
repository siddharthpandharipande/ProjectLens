from typing import List, Dict, Any
from app.models.code_metric import CodeMetric
from app.config import analysis_thresholds as thresholds

def detect_strengths(
    cm: CodeMetric,
    tech_list: List[Dict[str, Any]],
    doc_res: Dict[str, Any],
    git_res: Dict[str, Any],
    scanned_files: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generates evidence-backed project strengths.
    Only displays strengths supported by concrete repository findings.
    Limits to top 3-5 strongest findings.
    """
    strengths: List[Dict[str, Any]] = []

    # 1. Low Cyclomatic Complexity
    if cm and cm.average_complexity <= thresholds.HIGH_COMPLEXITY:
        strengths.append({
            "title": "Low Average Code Complexity",
            "description": f"Average cyclomatic complexity is {cm.average_complexity}, indicating clean and maintainable function logic.",
            "evidence": f"Average complexity: {cm.average_complexity} (threshold: {thresholds.HIGH_COMPLEXITY})"
        })

    # 2. Automated Test Suite Presence
    if cm and cm.test_file_count > 0:
        strengths.append({
            "title": "Automated Test Suite Included",
            "description": f"The codebase contains {cm.test_file_count} test file(s), demonstrating commitment to software verification.",
            "evidence": f"Found {cm.test_file_count} test file(s)"
        })

    # 3. Comprehensive Documentation
    doc_score = doc_res.get("score")
    if doc_score and doc_score >= 70.0:
        strengths.append({
            "title": "Comprehensive Project Documentation",
            "description": "The project includes detailed documentation covering setup, usage, and architecture.",
            "evidence": f"Documentation Integrity score: {doc_score}/100"
        })

    # 4. Frontend & Backend Layer Separation
    has_frontend = any(t.get("category") == "FRONTEND" for t in tech_list)
    has_backend = any(t.get("category") == "BACKEND" for t in tech_list)
    if has_frontend and has_backend:
        strengths.append({
            "title": "Clear Frontend & Backend Separation",
            "description": "Discovered distinct frontend and backend technology layers in the repository architecture.",
            "evidence": "Separate frontend and backend dependencies detected"
        })

    # 5. Modular File Organization
    if cm and cm.source_file_count >= 5:
        strengths.append({
            "title": "Modular Architecture",
            "description": f"Source code is partitioned cleanly across {cm.source_file_count} source files.",
            "evidence": f"{cm.source_file_count} source files identified"
        })

    # 6. Iterative Git Commit Track
    git_score = git_res.get("score")
    if git_score and git_score >= 60.0:
        strengths.append({
            "title": "Iterative Development Process",
            "description": "Git metadata confirms sustained commit activity across project development.",
            "evidence": f"Development Process score: {git_score}/100"
        })

    return strengths[:5]
