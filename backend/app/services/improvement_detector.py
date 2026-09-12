from typing import List, Dict, Any
from app.models.code_metric import CodeMetric
from app.config import analysis_thresholds as thresholds

def detect_improvements(
    cm: CodeMetric,
    failed_files_count: int,
    doc_res: Dict[str, Any],
    git_res: Dict[str, Any],
    coverage_text: str
) -> List[Dict[str, Any]]:
    """
    Generates evidence-backed areas for improvement with severity (info, warning, critical).
    Driven by configurable heuristics in analysis_thresholds.py.
    """
    improvements: List[Dict[str, Any]] = []

    # 1. High Complexity
    if cm and cm.average_complexity > thresholds.HIGH_COMPLEXITY:
        severity = "critical" if cm.average_complexity > thresholds.VERY_HIGH_COMPLEXITY else "warning"
        improvements.append({
            "title": "High Average Cyclomatic Complexity",
            "severity": severity,
            "description": f"Average complexity is {cm.average_complexity} (threshold: {thresholds.HIGH_COMPLEXITY}). Consider refactoring complex functions into smaller modules.",
            "evidence": f"Average complexity: {cm.average_complexity}, Maximum complexity: {cm.maximum_complexity}",
            "metric": cm.average_complexity
        })

    # 2. Missing Automated Tests
    if cm and cm.test_file_count == 0:
        improvements.append({
            "title": "No Automated Test Suite Detected",
            "severity": "warning",
            "description": "No automated test files were found in the codebase. Adding test cases improves code reliability.",
            "evidence": "0 test files detected",
            "metric": 0
        })

    # 3. Missing Coverage Report Artifact
    if coverage_text == "N/A":
        improvements.append({
            "title": "No Code Coverage Artifact Found",
            "severity": "info",
            "description": "No code coverage report artifact (e.g. coverage.xml, lcov.info, coverage.json) was detected.",
            "evidence": "No coverage artifact detected in project root",
            "metric": "N/A"
        })

    # 4. Incomplete Documentation
    doc_score = doc_res.get("score", 0.0)
    if doc_score < 50.0:
        improvements.append({
            "title": "Incomplete Project Documentation",
            "severity": "warning",
            "description": "Documentation lacks standard setup instructions or technical architecture descriptions.",
            "evidence": f"Documentation Integrity score: {doc_score}/100",
            "metric": doc_score
        })

    # 5. Missing Git History
    if git_res.get("status") == "N/A":
        improvements.append({
            "title": "Git Metadata Not Included",
            "severity": "info",
            "description": "The submitted archive did not contain `.git` commit history for development timeline tracking.",
            "evidence": "Git history was not included in the submitted project.",
            "metric": "N/A"
        })

    # 6. Syntax Parsing Warnings
    if failed_files_count > 0:
        improvements.append({
            "title": "Source Files Parsing Warnings",
            "severity": "warning",
            "description": f"{failed_files_count} file(s) encountered syntax parsing errors during analysis.",
            "evidence": f"{failed_files_count} file(s) failed static parsing",
            "metric": failed_files_count
        })

    # Sort improvements by severity: critical > warning > info
    severity_rank = {"critical": 0, "warning": 1, "info": 2}
    improvements.sort(key=lambda x: severity_rank.get(x["severity"], 9))

    return improvements
