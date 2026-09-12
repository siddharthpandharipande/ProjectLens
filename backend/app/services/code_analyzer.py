import ast
import re
from pathlib import Path
from typing import Dict, Any, List
import radon.complexity as cc

def analyze_line_counts(content: str, language: str) -> Dict[str, int]:
    """
    Calculate physical total lines, blank lines, comment lines, and code lines.
    """
    lines = content.splitlines()
    total = len(lines)
    blank = 0
    comment = 0
    code = 0
    
    in_block_comment = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue
            
        if language in {"Python"}:
            if stripped.startswith("#"):
                comment += 1
            else:
                code += 1
        elif language in {"JavaScript", "TypeScript", "JavaScript React", "TypeScript React", "Java", "C++", "C", "Go", "Rust", "C#"}:
            if in_block_comment:
                comment += 1
                if "*/" in stripped:
                    in_block_comment = False
            elif stripped.startswith("/*"):
                comment += 1
                if "*/" not in stripped:
                    in_block_comment = True
            elif stripped.startswith("//"):
                comment += 1
            else:
                code += 1
        elif language in {"HTML", "XML"}:
            if stripped.startswith("<!--"):
                comment += 1
            else:
                code += 1
        elif language in {"CSS"}:
            if stripped.startswith("/*"):
                comment += 1
            else:
                code += 1
        else:
            if stripped.startswith("#") or stripped.startswith("//"):
                comment += 1
            else:
                code += 1
                
    return {
        "lines_total": total,
        "lines_blank": blank,
        "lines_comment": comment,
        "lines_code": code,
    }

def analyze_python_ast(content: str) -> Dict[str, Any]:
    """
    Parse Python source code using AST and Radon to extract functions, classes, and complexity.
    """
    functions = 0
    classes = 0
    complexities = []
    
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions += 1
            elif isinstance(node, ast.ClassDef):
                classes += 1
                
        # Radon cyclomatic complexity
        blocks = cc.cc_visit(content)
        for b in blocks:
            complexities.append(b.complexity)
            
    except Exception as e:
        raise ValueError(f"Python AST/Radon parsing error: {str(e)}")
        
    avg_cc = float(sum(complexities) / len(complexities)) if complexities else 1.0
    max_cc = float(max(complexities)) if complexities else 1.0
    
    return {
        "function_count": functions,
        "class_count": classes,
        "average_complexity": round(avg_cc, 1),
        "maximum_complexity": round(max_cc, 1),
    }

def analyze_generic_code(content: str, language: str) -> Dict[str, Any]:
    """
    Fallback deterministic parser for non-Python source languages (JS, TS, Java, C++, C, Go).
    Uses pattern signatures to count functions, classes, and control flow branches for complexity.
    """
    functions = 0
    classes = 0
    complexities = [1.0]  # Base score
    
    # Class definitions regex pattern
    class_pattern = re.compile(r'\b(class|interface|enum|struct)\s+\w+')
    classes = len(class_pattern.findall(content))
    
    # Function definitions regex pattern
    func_pattern = re.compile(r'\b(function|def|fn|public|private|protected|static|async)\s+\w+\s*\(')
    functions = len(func_pattern.findall(content))
    
    # Control flow complexity branches: if, else if, for, while, switch, catch, &&, ||
    branches = len(re.findall(r'\b(if|else\s+if|for|while|switch|case|catch)\b|\&\&|\|\|', content))
    
    if functions > 0:
        avg_cc = float(1.0 + (branches / functions))
        max_cc = float(1.0 + min(branches, 15))
    else:
        avg_cc = float(1.0 + (branches * 0.2))
        max_cc = float(1.0 + branches)
        
    return {
        "function_count": functions,
        "class_count": classes,
        "average_complexity": round(avg_cc, 1),
        "maximum_complexity": round(max_cc, 1),
    }

def analyze_single_file(abs_path: Path, language: str, file_type: str) -> Dict[str, Any]:
    """
    Analyze a single source file with per-file exception handling.
    If parsing fails, returns parse_status="failed" without crashing.
    """
    result = {
        "lines_total": 0,
        "lines_code": 0,
        "lines_comment": 0,
        "lines_blank": 0,
        "function_count": 0,
        "class_count": 0,
        "average_complexity": 0.0,
        "maximum_complexity": 0.0,
        "parse_status": "success",
        "error_message": None,
    }
    
    try:
        if not abs_path.exists() or abs_path.stat().st_size > 5_000_000:
            result["parse_status"] = "skipped"
            return result
            
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # 1. Line counts
        line_metrics = analyze_line_counts(content, language)
        result.update(line_metrics)
        
        # 2. Structural & Complexity metrics for source/test files
        if file_type in {"source", "test"}:
            if language == "Python":
                ast_metrics = analyze_python_ast(content)
                result.update(ast_metrics)
            else:
                generic_metrics = analyze_generic_code(content, language)
                result.update(generic_metrics)
                
    except Exception as e:
        result["parse_status"] = "failed"
        result["error_message"] = str(e)
        
    return result

def detect_test_coverage(scanned_files: List[Dict[str, Any]]) -> str:
    """
    Parses actual test coverage artifacts (coverage.xml, coverage.json, lcov.info, etc.) if present.
    If no coverage report exists, returns "N/A".
    """
    target_coverage_files = {"coverage.xml", "coverage.json", "lcov.info", ".coverage"}

    for sf in scanned_files:
        fn_lower = sf.get("filename", "").lower()
        if fn_lower in target_coverage_files:
            abs_path = sf.get("abs_path")
            if abs_path and isinstance(abs_path, Path) and abs_path.exists():
                try:
                    content = abs_path.read_text(encoding="utf-8", errors="ignore")

                    # XML coverage parsing line-rate="0.85"
                    match = re.search(r'line-rate=["\']([0-9\.]+)["\']', content)
                    if match:
                        rate = float(match.group(1))
                        pct = round(rate * 100 if rate <= 1.0 else rate, 1)
                        return f"{pct}%"

                    # JSON coverage parsing "pct": 85.5
                    match_json = re.search(r'"lines":\s*\{\s*"total":\s*\d+,\s*"covered":\s*\d+,\s*"pct":\s*([0-9\.]+)', content)
                    if match_json:
                        return f"{round(float(match_json.group(1)), 1)}%"
                except Exception:
                    pass

    return "N/A"
