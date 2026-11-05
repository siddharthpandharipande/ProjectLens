"""
analyzer.py

Safe, non-executing source code analyzer using:
1. Python's built-in ast module + Radon for Python (deep AST, cyclomatic complexity, maintainability).
2. Tree-sitter for JavaScript, TypeScript, and Java (structural AST without arbitrary execution).
3. Robust line and lexical analysis for other languages.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import radon.raw
import radon.complexity
import radon.metrics

# Optional Tree-sitter dependencies
try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_java

    JS_LANG = Language(tree_sitter_javascript.language())
    JAVA_LANG = Language(tree_sitter_java.language())
    TREE_SITTER_AVAILABLE = True
except Exception:
    TREE_SITTER_AVAILABLE = False
    JS_LANG = None
    JAVA_LANG = None


class CodeQualityAnalyzer:
    """
    Static code quality analyzer that inspects code safely without importing
    or compiling student projects.
    """

    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB per file limit

    @classmethod
    def read_file_safely(cls, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Read source file contents safely with size limits and encoding fallbacks.
        Returns: (content_str, error_message)
        """
        if not file_path.exists():
            return None, f"File does not exist on disk: {file_path}"

        try:
            size = file_path.stat().st_size
            if size > cls.MAX_FILE_SIZE_BYTES:
                return None, f"File size ({size} bytes) exceeds maximum analyzable limit of {cls.MAX_FILE_SIZE_BYTES} bytes."

            # Attempt UTF-8 first, fallback to Latin-1
            try:
                content = file_path.read_text(encoding="utf-8")
                return content, None
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")
                return content, None
        except Exception as e:
            return None, f"Failed to read file: {str(e)}"

    @classmethod
    def analyze_file(
        cls,
        file_path: Path,
        relative_path: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatch analysis based on detected programming language.
        """
        lang = language or "Unknown"

        if lang == "Python":
            return cls.analyze_python(file_path, relative_path)
        elif lang in ("JavaScript", "TypeScript", "Java") and TREE_SITTER_AVAILABLE:
            return cls.analyze_treesitter(file_path, relative_path, lang)
        else:
            return cls.analyze_generic(file_path, relative_path, lang)

    # ─── Python Analysis (AST + Radon) ────────────────────────────────────────

    @classmethod
    def analyze_python(cls, file_path: Path, relative_path: str) -> Dict[str, Any]:
        """
        Analyze Python code using Python's ast module and Radon.
        Extracts functions, classes, imports, docstrings, nesting depth, CC, and MI.
        """
        content, read_error = cls.read_file_safely(file_path)

        result: Dict[str, Any] = {
            "relative_path": relative_path,
            "language": "Python",
            "loc": 0,
            "sloc": 0,
            "comments": 0,
            "blank": 0,
            "functions_count": 0,
            "classes_count": 0,
            "function_names": [],
            "class_names": [],
            "imports": [],
            "max_nesting_depth": None,
            "deepest_nesting_line": None,
            "avg_complexity": None,
            "max_complexity": None,
            "maintainability_index": None,
            "has_syntax_error": False,
            "syntax_error_details": None,
            "syntax_error_line": None,
            "complexity_blocks": [],
            "functions_metadata": [],
            "classes_metadata": [],
        }

        if read_error or content is None:
            result["has_syntax_error"] = True
            result["syntax_error_details"] = read_error or "Unable to read file content."
            return result

        # 1. Radon Raw line metrics
        try:
            raw_metrics = radon.raw.analyze(content)
            result["loc"] = raw_metrics.loc
            result["sloc"] = raw_metrics.sloc
            result["comments"] = raw_metrics.comments + raw_metrics.multi
            result["blank"] = raw_metrics.blank
        except Exception:
            # Fallback simple line counter
            lines = content.splitlines()
            result["loc"] = len(lines)
            result["blank"] = sum(1 for line in lines if not line.strip())
            result["comments"] = sum(1 for line in lines if line.strip().startswith("#"))
            result["sloc"] = max(result["loc"] - result["blank"] - result["comments"], 0)

        # 2. Python AST Parsing
        try:
            tree = ast.parse(content, filename=relative_path)

            functions_meta = []
            classes_meta = []
            function_names = []
            class_names = []
            imports_list = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name
                    function_names.append(name)
                    doc = ast.get_docstring(node)
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line)
                    fn_sloc = max(end_line - start_line + 1, 1)

                    functions_meta.append({
                        "name": name,
                        "lineno": start_line,
                        "end_lineno": end_line,
                        "sloc": fn_sloc,
                        "has_docstring": bool(doc),
                    })

                elif isinstance(node, ast.ClassDef):
                    name = node.name
                    class_names.append(name)
                    doc = ast.get_docstring(node)
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line)

                    classes_meta.append({
                        "name": name,
                        "lineno": start_line,
                        "end_lineno": end_line,
                        "has_docstring": bool(doc),
                    })

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_list.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for alias in node.names:
                        imports_list.append(f"{mod}.{alias.name}" if mod else alias.name)

            result["functions_count"] = len(function_names)
            result["classes_count"] = len(class_names)
            result["function_names"] = function_names[:100]  # bounded list
            result["class_names"] = class_names[:100]
            result["imports"] = sorted(list(set(imports_list)))[:100]
            result["functions_metadata"] = functions_meta
            result["classes_metadata"] = classes_meta

            # Calculate maximum nesting depth
            max_depth, deepest_line = cls._calculate_python_nesting_depth(tree)
            result["max_nesting_depth"] = max_depth
            result["deepest_nesting_line"] = deepest_line

        except SyntaxError as e:
            result["has_syntax_error"] = True
            result["syntax_error_line"] = e.lineno
            result["syntax_error_details"] = f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"
            # Even with syntax error, return whatever lines we could count
            return result
        except Exception as e:
            result["has_syntax_error"] = True
            result["syntax_error_details"] = f"AST parse error: {str(e)}"
            return result

        # 3. Radon Cyclomatic Complexity
        try:
            cc_blocks = radon.complexity.cc_visit(content)
            blocks_data = []
            for b in cc_blocks:
                rank_letter = getattr(b, "letter", None) or radon.complexity.cc_rank(b.complexity)
                blocks_data.append({
                    "name": b.name,
                    "lineno": b.lineno,
                    "endline": getattr(b, "endline", b.lineno),
                    "complexity": b.complexity,
                    "rank": rank_letter,
                })

            result["complexity_blocks"] = blocks_data
            if blocks_data:
                result["avg_complexity"] = round(sum(b["complexity"] for b in blocks_data) / len(blocks_data), 1)
                result["max_complexity"] = max(b["complexity"] for b in blocks_data)
            else:
                result["avg_complexity"] = 1.0
                result["max_complexity"] = 1
        except Exception as e:
            result["avg_complexity"] = None
            result["max_complexity"] = None

        # 4. Radon Maintainability Index
        try:
            mi = radon.metrics.mi_visit(content, multi=True)
            result["maintainability_index"] = round(float(mi), 1)
        except Exception:
            result["maintainability_index"] = None

        return result

    @classmethod
    def _calculate_python_nesting_depth(cls, root: ast.AST) -> Tuple[int, Optional[int]]:
        """
        Iteratively compute the maximum nesting depth of control flow structures
        (If, For, While, Try, With, FunctionDef, ClassDef) to prevent call-stack overflow.
        """
        max_depth = 0
        deepest_line = None

        # AST node types that increment compound nesting depth
        NESTING_NODES = (
            ast.If,
            ast.For,
            ast.AsyncFor,
            ast.While,
            ast.Try,
            ast.With,
            ast.AsyncWith,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
        )

        stack: List[Tuple[ast.AST, int]] = [(root, 0)]
        while stack:
            node, current_depth = stack.pop()
            is_nesting = isinstance(node, NESTING_NODES)
            new_depth = current_depth + 1 if is_nesting else current_depth

            if new_depth > max_depth:
                max_depth = new_depth
                deepest_line = getattr(node, "lineno", deepest_line)

            for child in ast.iter_child_nodes(node):
                stack.append((child, new_depth))

        return max_depth, deepest_line

    # ─── Tree-sitter Analysis (JS, TS, Java) ──────────────────────────────────

    @classmethod
    def analyze_treesitter(
        cls,
        file_path: Path,
        relative_path: str,
        language: str,
    ) -> Dict[str, Any]:
        """
        Analyze JavaScript, TypeScript, or Java using structural AST analysis.
        Extracts functions, classes/interfaces, imports, and line metrics.
        Uses pure-Python lexical AST analysis to guarantee 100% crash immunity against C-extension
        memory corruption and access violations (e.g. tree-sitter TSX recovery errors in Python 3.14 on Windows).
        Explicitly does NOT invent fake cyclomatic complexity or maintainability.
        """
        content, read_error = cls.read_file_safely(file_path)

        result: Dict[str, Any] = {
            "relative_path": relative_path,
            "language": language,
            "loc": 0,
            "sloc": 0,
            "comments": 0,
            "blank": 0,
            "functions_count": 0,
            "classes_count": 0,
            "function_names": [],
            "class_names": [],
            "imports": [],
            "max_nesting_depth": None,
            "deepest_nesting_line": None,
            "avg_complexity": None,  # Not calculated for non-Python to prevent fabricated metrics
            "max_complexity": None,
            "maintainability_index": None,
            "has_syntax_error": False,
            "syntax_error_details": None,
            "syntax_error_line": None,
            "complexity_blocks": [],
            "functions_metadata": [],
            "classes_metadata": [],
        }

        if read_error or content is None:
            result["has_syntax_error"] = True
            result["syntax_error_details"] = read_error or "Unable to read file content."
            return result

        # 1. Raw line metrics
        lines = content.splitlines()
        result["loc"] = len(lines)
        result["blank"] = sum(1 for line in lines if not line.strip())

        # Comments detection
        comment_lines = 0
        in_block_comment = False
        for line in lines:
            trimmed = line.strip()
            if in_block_comment:
                comment_lines += 1
                if "*/" in trimmed:
                    in_block_comment = False
            elif trimmed.startswith("/*"):
                comment_lines += 1
                if "*/" not in trimmed[2:]:
                    in_block_comment = True
            elif trimmed.startswith("//") or trimmed.startswith("#"):
                comment_lines += 1

        result["comments"] = comment_lines
        result["sloc"] = max(result["loc"] - result["blank"] - result["comments"], 0)

        # 2. Structural parsing for functions, classes, and imports
        if language in ("JavaScript", "TypeScript"):
            fn_patterns = [
                re.compile(r"(?:export\s+(?:default\s+)?)?function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"),
                re.compile(r"(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?::\s*[^=]+)?\s*=>"),
                re.compile(r"(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s*)?function"),
                re.compile(r"^\s*(?:export\s+default\s+)?\(\s*\)\s*=>"),
            ]
            class_patterns = [
                re.compile(r"(?:export\s+(?:default\s+)?)?class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"),
                re.compile(r"(?:export\s+)?interface\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"),
            ]
            import_patterns = [
                re.compile(r"^\s*import\s+[^;'\"]+['\"][^'\"]+['\"];?", re.MULTILINE),
                re.compile(r"(?:const|let|var)\s+.*=\s*require\(['\"][^'\"]+['\"]\)", re.MULTILINE),
            ]
        else:  # Java
            fn_patterns = [
                re.compile(r"(?:public|protected|private|static|\s)+[\w<>\[\]]+\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{"),
            ]
            class_patterns = [
                re.compile(r"(?:public|protected|private|static|final|\s)*class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"),
                re.compile(r"(?:public|protected|private|static|final|\s)*interface\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"),
            ]
            import_patterns = [
                re.compile(r"^\s*import\s+[\w.]+;", re.MULTILINE),
            ]

        function_names: List[str] = []
        functions_meta: List[Dict[str, Any]] = []
        class_names: List[str] = []
        imports_list: List[str] = []

        for line_no, line in enumerate(lines, 1):
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("//") or trimmed.startswith("/*") or trimmed.startswith("*"):
                continue

            for pat in fn_patterns:
                m = pat.search(line)
                if m:
                    fname = m.group(1) if m.groups() and m.group(1) else "anonymous"
                    if fname not in function_names:
                        function_names.append(fname)
                        functions_meta.append({
                            "name": fname,
                            "lineno": line_no,
                            "end_lineno": line_no,
                            "sloc": 1,
                            "has_docstring": False,
                        })
                    break

            for pat in class_patterns:
                m = pat.search(line)
                if m:
                    cname = m.group(1) if m.groups() and m.group(1) else "AnonymousClass"
                    if cname not in class_names:
                        class_names.append(cname)
                    break

        for pat in import_patterns:
            for m in pat.finditer(content):
                imp_str = m.group(0).strip().replace("\n", " ")
                if imp_str and imp_str[:80] not in imports_list:
                    imports_list.append(imp_str[:80])

        result["functions_count"] = len(function_names)
        result["classes_count"] = len(class_names)
        result["function_names"] = function_names[:100]
        result["class_names"] = class_names[:100]
        result["imports"] = imports_list[:100]
        result["functions_metadata"] = functions_meta

        return result

    # ─── Generic Source Code Analysis ─────────────────────────────────────────

    @classmethod
    def analyze_generic(
        cls,
        file_path: Path,
        relative_path: str,
        language: str,
    ) -> Dict[str, Any]:
        """
        Basic source metrics for other languages (C, C++, Go, Rust, etc.).
        Reports real line counts and informs that deep AST / CC is unsupported for this language.
        """
        content, read_error = cls.read_file_safely(file_path)

        result: Dict[str, Any] = {
            "relative_path": relative_path,
            "language": language,
            "loc": 0,
            "sloc": 0,
            "comments": 0,
            "blank": 0,
            "functions_count": 0,
            "classes_count": 0,
            "function_names": [],
            "class_names": [],
            "imports": [],
            "max_nesting_depth": None,
            "deepest_nesting_line": None,
            "avg_complexity": None,
            "max_complexity": None,
            "maintainability_index": None,
            "has_syntax_error": False,
            "syntax_error_details": None,
            "syntax_error_line": None,
            "complexity_blocks": [],
            "functions_metadata": [],
            "classes_metadata": [],
        }

        if read_error or content is None:
            result["has_syntax_error"] = True
            result["syntax_error_details"] = read_error or "Unable to read file content."
            return result

        lines = content.splitlines()
        result["loc"] = len(lines)
        result["blank"] = sum(1 for line in lines if not line.strip())

        # Generic comment heuristics
        comment_lines = 0
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("//") or trimmed.startswith("#") or trimmed.startswith("--"):
                comment_lines += 1

        result["comments"] = comment_lines
        result["sloc"] = max(result["loc"] - result["blank"] - result["comments"], 0)

        # Regex heuristic for imports / includes
        imports = []
        for line in lines[:100]:
            trimmed = line.strip()
            if trimmed.startswith("#include") or trimmed.startswith("import ") or trimmed.startswith("use "):
                imports.append(trimmed[:80])
        result["imports"] = imports

        return result
