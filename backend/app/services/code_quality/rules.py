"""
rules.py

Configurable, transparent rules module for Code Quality findings.
No LLM is used; all findings are driven by deterministic structural inspection,
AST metrics, and Radon calculations.
"""

from typing import List, Dict, Any, Optional

# ─── Configurable Thresholds ──────────────────────────────────────────────────
# CC <= 5: simple; 6-10: moderate; 11-15: high risk; >15: critical complexity
CYCLOMATIC_COMPLEXITY_WARNING_THRESHOLD: int = 10
CYCLOMATIC_COMPLEXITY_CRITICAL_THRESHOLD: int = 15

# Functions exceeding 50 SLOC often violate the Single Responsibility Principle
FUNCTION_SLOC_WARNING_THRESHOLD: int = 50
FUNCTION_SLOC_CRITICAL_THRESHOLD: int = 100

# Nesting depth > 4 introduces cognitive strain and branching risk
MAX_NESTING_WARNING_THRESHOLD: int = 4
MAX_NESTING_CRITICAL_THRESHOLD: int = 6

# Radon Maintainability Index: <20 is considered difficult to maintain (Rank C)
LOW_MAINTAINABILITY_INDEX_THRESHOLD: float = 20.0

# Only flag missing docstrings if a function/class has significant implementation
DOCSTRING_MIN_SLOC_THRESHOLD: int = 15


def evaluate_quality_rules(
    file_metrics: List[Dict[str, Any]],
    project_metrics: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Evaluate deterministic code-quality rules across all analyzed files.
    Every finding includes:
      - rule_id (stable code)
      - title
      - explanation
      - severity ("High" | "Medium" | "Low" | "Info")
      - file_path
      - line_number
      - line_range
      - metric_evidence
      - suggestion
    """
    findings: List[Dict[str, Any]] = []

    for f in file_metrics:
        rel_path = f.get("relative_path", "")
        lang = f.get("language") or "Unknown"

        # Rule 1: Syntax / Parse Error (High)
        if f.get("has_syntax_error"):
            details = f.get("syntax_error_details") or "Syntax error encountered during parsing."
            findings.append({
                "rule_id": "PY-SYNTAX-ERR" if lang == "Python" else "GEN-SYNTAX-ERR",
                "title": f"Syntax Error in {lang} Source File",
                "explanation": f"The parser failed to process '{rel_path}' due to an unrecoverable syntax error.",
                "severity": "High",
                "file_path": rel_path,
                "line_number": f.get("syntax_error_line"),
                "line_range": None,
                "metric_evidence": details,
                "suggestion": "Correct the syntax error at the indicated line to restore code validity.",
            })

        # Rule 2: Cyclomatic Complexity (Critical / Warning)
        cc_blocks = f.get("complexity_blocks") or []
        for block in cc_blocks:
            cc = block.get("complexity", 1)
            name = block.get("name", "function")
            lineno = block.get("lineno")
            end_lineno = block.get("endline")

            if cc > CYCLOMATIC_COMPLEXITY_CRITICAL_THRESHOLD:
                findings.append({
                    "rule_id": "PY-CC-CRITICAL",
                    "title": f"Critical Cyclomatic Complexity in '{name}'",
                    "explanation": (
                        f"Function or method '{name}' has a cyclomatic complexity of {cc}, "
                        f"exceeding the critical threshold of {CYCLOMATIC_COMPLEXITY_CRITICAL_THRESHOLD}."
                    ),
                    "severity": "High",
                    "file_path": rel_path,
                    "line_number": lineno,
                    "line_range": [lineno, end_lineno] if lineno and end_lineno else None,
                    "metric_evidence": f"Cyclomatic Complexity = {cc} (threshold: {CYCLOMATIC_COMPLEXITY_CRITICAL_THRESHOLD})",
                    "suggestion": "Decompose this function into smaller, single-purpose helper functions or use lookup tables.",
                })
            elif cc > CYCLOMATIC_COMPLEXITY_WARNING_THRESHOLD:
                findings.append({
                    "rule_id": "PY-CC-WARNING",
                    "title": f"Elevated Cyclomatic Complexity in '{name}'",
                    "explanation": (
                        f"Function or method '{name}' has a cyclomatic complexity of {cc}, "
                        f"exceeding the recommended threshold of {CYCLOMATIC_COMPLEXITY_WARNING_THRESHOLD}."
                    ),
                    "severity": "Medium",
                    "file_path": rel_path,
                    "line_number": lineno,
                    "line_range": [lineno, end_lineno] if lineno and end_lineno else None,
                    "metric_evidence": f"Cyclomatic Complexity = {cc} (threshold: {CYCLOMATIC_COMPLEXITY_WARNING_THRESHOLD})",
                    "suggestion": "Simplify conditional branches and consider early returns.",
                })

        # Rule 3: Function Length (SLOC)
        functions_meta = f.get("functions_metadata") or []
        for fn in functions_meta:
            fn_name = fn.get("name", "function")
            fn_sloc = fn.get("sloc", 0)
            fn_line = fn.get("lineno")
            fn_end = fn.get("end_lineno")

            if fn_sloc > FUNCTION_SLOC_CRITICAL_THRESHOLD:
                findings.append({
                    "rule_id": "PY-FUNC-VERY-LONG",
                    "title": f"Very Long Function '{fn_name}'",
                    "explanation": f"Function '{fn_name}' spans {fn_sloc} source lines of code, exceeding the limit of {FUNCTION_SLOC_CRITICAL_THRESHOLD}.",
                    "severity": "Medium",
                    "file_path": rel_path,
                    "line_number": fn_line,
                    "line_range": [fn_line, fn_end] if fn_line and fn_end else None,
                    "metric_evidence": f"Function SLOC = {fn_sloc} (threshold: {FUNCTION_SLOC_CRITICAL_THRESHOLD})",
                    "suggestion": "Refactor into modular subroutines to improve readability and test isolation.",
                })
            elif fn_sloc > FUNCTION_SLOC_WARNING_THRESHOLD:
                findings.append({
                    "rule_id": "PY-FUNC-LONG",
                    "title": f"Long Function '{fn_name}'",
                    "explanation": f"Function '{fn_name}' spans {fn_sloc} source lines of code, exceeding {FUNCTION_SLOC_WARNING_THRESHOLD}.",
                    "severity": "Low",
                    "file_path": rel_path,
                    "line_number": fn_line,
                    "line_range": [fn_line, fn_end] if fn_line and fn_end else None,
                    "metric_evidence": f"Function SLOC = {fn_sloc} (threshold: {FUNCTION_SLOC_WARNING_THRESHOLD})",
                    "suggestion": "Consider breaking long workflows into distinct steps.",
                })

        # Rule 4: Deep Nesting Structure
        nesting = f.get("max_nesting_depth")
        if nesting is not None:
            if nesting > MAX_NESTING_CRITICAL_THRESHOLD:
                findings.append({
                    "rule_id": "PY-NESTING-CRITICAL",
                    "title": "Severe Control Flow Nesting Depth",
                    "explanation": f"Maximum nesting depth of {nesting} exceeds acceptable limit of {MAX_NESTING_CRITICAL_THRESHOLD}.",
                    "severity": "High",
                    "file_path": rel_path,
                    "line_number": f.get("deepest_nesting_line"),
                    "line_range": None,
                    "metric_evidence": f"Max Nesting Depth = {nesting} (threshold: {MAX_NESTING_CRITICAL_THRESHOLD})",
                    "suggestion": "Flatten logic with guard clauses, early returns, or polymorphism.",
                })
            elif nesting > MAX_NESTING_WARNING_THRESHOLD:
                findings.append({
                    "rule_id": "PY-NESTING-DEEP",
                    "title": "Deep Control Flow Nesting",
                    "explanation": f"Maximum nesting depth of {nesting} exceeds recommended threshold of {MAX_NESTING_WARNING_THRESHOLD}.",
                    "severity": "Medium",
                    "file_path": rel_path,
                    "line_number": f.get("deepest_nesting_line"),
                    "line_range": None,
                    "metric_evidence": f"Max Nesting Depth = {nesting} (threshold: {MAX_NESTING_WARNING_THRESHOLD})",
                    "suggestion": "Use guard clauses and early exits to avoid deep indentation trees.",
                })

        # Rule 5: Low Maintainability Index (Radon MI)
        mi = f.get("maintainability_index")
        if mi is not None and mi < LOW_MAINTAINABILITY_INDEX_THRESHOLD:
            findings.append({
                "rule_id": "PY-LOW-MAINTAINABILITY",
                "title": "Low Maintainability Index (Radon Rank C)",
                "explanation": f"File maintainability index is {mi:.1f}, below the acceptable threshold of {LOW_MAINTAINABILITY_INDEX_THRESHOLD}.",
                "severity": "Medium",
                "file_path": rel_path,
                "line_number": 1,
                "line_range": None,
                "metric_evidence": f"Maintainability Index = {mi:.1f} / 100",
                "suggestion": "Reduce cyclomatic complexity and physical volume in this module.",
            })

        # Rule 6: Missing Docstring in Non-Trivial Functions / Classes
        for fn in functions_meta:
            if not fn.get("has_docstring") and fn.get("sloc", 0) >= DOCSTRING_MIN_SLOC_THRESHOLD:
                findings.append({
                    "rule_id": "PY-DOC-MISSING",
                    "title": f"Missing Docstring in '{fn.get('name')}'",
                    "explanation": f"Substantial function '{fn.get('name')}' ({fn.get('sloc')} SLOC) lacks a documentation docstring.",
                    "severity": "Info",
                    "file_path": rel_path,
                    "line_number": fn.get("lineno"),
                    "line_range": None,
                    "metric_evidence": f"SLOC = {fn.get('sloc')} without docstring",
                    "suggestion": "Add a descriptive docstring explaining arguments, return value, and expected behavior.",
                })

        # Rule 7: Empty Source File
        if f.get("sloc", 0) == 0 and not f.get("has_syntax_error"):
            # Check if comments or blank exist, but no real code
            findings.append({
                "rule_id": "GEN-EMPTY-SOURCE",
                "title": "Empty Source Code File",
                "explanation": f"Source file '{rel_path}' contains 0 source lines of code.",
                "severity": "Info",
                "file_path": rel_path,
                "line_number": 1,
                "line_range": None,
                "metric_evidence": "SLOC = 0",
                "suggestion": "Implement the intended logic or remove the placeholder file.",
            })

    return findings
