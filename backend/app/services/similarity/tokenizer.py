"""
tokenizer.py

Language-aware tokenization, normalization, and token-based similarity analysis.
Calculates Jaccard similarity on token shingles, extracts matched statement spans,
and identifies source line ranges and snippet evidence.

Normalization Policy:
- Whitespace & Formatting: Normalizes indentation, line breaks, and whitespace between tokens.
- Comments: Strips line comments and block comments to prevent superficial comment modifications from skewing similarity.
- Identifiers & Literals: Preserves keywords and structural operators; normalizes variable names where appropriate for token fingerprinting.
- Empty Files: Explicitly returns 0.0 similarity if both token sets are empty to avoid false 100% matches.

Limitations:
- Python: Uses standard library tokenize; handles all valid Python syntax. Syntax errors fall back to regex tokenization.
- JS/TS/Java: Tokenized via regex-based lexer or Tree-sitter leaf tokens, stripping comments and formatting.
- Header boilerplate: Leading comment blocks and standard license headers are stripped during normalization.
"""

import io
import re
import tokenize
from typing import List, Tuple, Set, Dict, Any, Optional


class CodeTokenizer:
    """Tokenizer and shingle comparison service for source code."""

    SHINGLE_SIZE = 4  # 4-token shingles

    # Boilerplate patterns to exclude (licenses, standard auto-generated headers)
    BOILERPLATE_PATTERNS = [
        re.compile(r"^\s*//\s*Copyright.*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*#\s*Copyright.*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*/\*.*Copyright.*?\*/", re.IGNORECASE | re.DOTALL),
        re.compile(r"^\s*#\s*-\*- coding:.*$", re.MULTILINE),
    ]

    @classmethod
    def strip_boilerplate(cls, code: str) -> str:
        """Strip standard license headers and encoding cookies."""
        cleaned = code
        for pat in cls.BOILERPLATE_PATTERNS:
            cleaned = pat.sub("", cleaned)
        return cleaned

    @classmethod
    def tokenize_python(cls, code: str) -> List[Tuple[str, int]]:
        """
        Tokenize Python source using standard library tokenize module.
        Returns list of (normalized_token_str, line_number).
        Ignores comments, encoding headers, and pure formatting whitespace.
        """
        code = cls.strip_boilerplate(code)
        tokens: List[Tuple[str, int]] = []
        try:
            reader = io.BytesIO(code.encode("utf-8")).readline
            for tok in tokenize.tokenize(reader):
                tok_type = tok.type
                tok_val = tok.string.strip()
                tok_line = tok.start[0]

                # Skip comment tokens, encoding markers, and empty whitespace
                if tok_type in (
                    tokenize.COMMENT,
                    tokenize.ENCODING,
                    tokenize.NL,
                    tokenize.NEWLINE,
                    tokenize.INDENT,
                    tokenize.DEDENT,
                ):
                    continue

                if not tok_val:
                    continue

                # Normalize string literals if needed or keep compact
                if tok_type == tokenize.STRING:
                    tok_val = '""'
                elif tok_type == tokenize.NUMBER:
                    tok_val = "0"

                tokens.append((tok_val, tok_line))
        except Exception:
            # Fallback to generic regex tokenizer if syntax is malformed
            return cls.tokenize_generic(code)

        return tokens

    @classmethod
    def tokenize_generic(cls, code: str) -> List[Tuple[str, int]]:
        """
        Generic language-aware tokenizer for JS, TS, Java, and other languages.
        Strips block and line comments, normalizes whitespace and literals.
        Returns list of (normalized_token_str, line_number).
        """
        code = cls.strip_boilerplate(code)
        tokens: List[Tuple[str, int]] = []

        lines = code.splitlines()
        in_block_comment = False

        # Token pattern: matches identifiers, keywords, numbers, string literals, and operators
        token_pattern = re.compile(
            r"([a-zA-Z_$][a-zA-Z0-9_$]*|\"[^\"]*\"|'[^']*'|`[^`]*`|\d+\.?\d*|[+\-*/%=!<>]=?|&&|\|\||[{}()\[\],;])"
        )

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line

            # Handle block comments
            if in_block_comment:
                if "*/" in line:
                    line = line.split("*/", 1)[1]
                    in_block_comment = False
                else:
                    continue

            if "/*" in line:
                before, after = line.split("/*", 1)
                if "*/" in after:
                    line = before + " " + after.split("*/", 1)[1]
                else:
                    line = before
                    in_block_comment = True

            # Strip line comment
            for comment_char in ("//", "#"):
                if comment_char in line:
                    line = line.split(comment_char, 1)[0]

            line = line.strip()
            if not line:
                continue

            for m in token_pattern.finditer(line):
                tok = m.group(1).strip()
                if not tok:
                    continue
                # Normalize string and number literals
                if (tok.startswith('"') and tok.endswith('"')) or (
                    tok.startswith("'") and tok.endswith("'")
                ) or (tok.startswith("`") and tok.endswith("`")):
                    tok = '""'
                elif re.match(r"^\d+\.?\d*$", tok):
                    tok = "0"

                tokens.append((tok, line_no))

        return tokens

    @classmethod
    def tokenize_file(cls, code: str, language: Optional[str]) -> List[Tuple[str, int]]:
        """Route to appropriate language tokenizer."""
        lang = (language or "").lower()
        if lang == "python":
            return cls.tokenize_python(code)
        return cls.tokenize_generic(code)

    @classmethod
    def create_shingles(cls, tokens: List[Tuple[str, int]], k: int = 4) -> Set[str]:
        """Convert list of token tuples into a set of k-token shingles."""
        if len(tokens) < k:
            if tokens:
                return {"_".join(t[0] for t in tokens)}
            return set()

        shingles: Set[str] = set()
        for i in range(len(tokens) - k + 1):
            shingle = "_".join(tokens[j][0] for j in range(i, i + k))
            shingles.add(shingle)
        return shingles

    @classmethod
    def calculate_token_similarity(
        cls,
        code_a: str,
        code_b: str,
        lang_a: Optional[str] = None,
        lang_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute token Jaccard similarity and extract matching evidence.
        Returns:
            dict containing:
            - token_similarity (float 0.0 - 100.0)
            - identical_statements (int)
            - current_lines (Tuple[int, int])
            - matched_lines (Tuple[int, int])
            - current_snippet (str)
            - matched_snippet (str)
        """
        toks_a = cls.tokenize_file(code_a, lang_a)
        toks_b = cls.tokenize_file(code_b, lang_b)

        # Empty files check
        if not toks_a or not toks_b:
            return {
                "token_similarity": 0.0,
                "identical_statements": 0,
                "current_lines": (1, 1),
                "matched_lines": (1, 1),
                "current_snippet": "",
                "matched_snippet": "",
            }

        shingles_a = cls.create_shingles(toks_a, cls.SHINGLE_SIZE)
        shingles_b = cls.create_shingles(toks_b, cls.SHINGLE_SIZE)

        if not shingles_a or not shingles_b:
            jaccard = 0.0
        else:
            intersection = shingles_a.intersection(shingles_b)
            union = shingles_a.union(shingles_b)
            jaccard = (len(intersection) / len(union)) if union else 0.0

        similarity_pct = round(jaccard * 100.0, 1)

        # Find matching statements and line ranges
        # Compare normalized non-empty lines between file A and file B
        lines_a = [l.strip() for l in code_a.splitlines()]
        lines_b = [l.strip() for l in code_b.splitlines()]

        # Filter out empty or pure brace lines
        meaningful_a = {l: i + 1 for i, l in enumerate(lines_a) if len(l) > 4 and not l in ("{", "}", ");", "pass")}
        meaningful_b = {l: i + 1 for i, l in enumerate(lines_b) if len(l) > 4 and not l in ("{", "}", ");", "pass")}

        common_lines = set(meaningful_a.keys()).intersection(set(meaningful_b.keys()))
        identical_statements = len(common_lines)

        current_lines = (1, max(len(lines_a), 1))
        matched_lines = (1, max(len(lines_b), 1))
        current_snippet = ""
        matched_snippet = ""

        if common_lines:
            # Locate first and last line numbers in A and B where common lines appear
            a_line_nums = sorted([meaningful_a[l] for l in common_lines])
            b_line_nums = sorted([meaningful_b[l] for l in common_lines])

            cur_start = max(1, a_line_nums[0])
            cur_end = min(len(lines_a), a_line_nums[-1])
            mat_start = max(1, b_line_nums[0])
            mat_end = min(len(lines_b), b_line_nums[-1])

            # Clamp snippet size to max 12 lines for display
            cur_end_display = min(cur_start + 11, cur_end)
            mat_end_display = min(mat_start + 11, mat_end)

            current_lines = (cur_start, cur_end)
            matched_lines = (mat_start, mat_end)

            current_snippet = "\n".join(lines_a[cur_start - 1 : cur_end_display])
            matched_snippet = "\n".join(lines_b[mat_start - 1 : mat_end_display])
        else:
            # Fallback preview: first few lines
            current_snippet = "\n".join(lines_a[:8]) if lines_a else ""
            matched_snippet = "\n".join(lines_b[:8]) if lines_b else ""

        return {
            "token_similarity": similarity_pct,
            "identical_statements": identical_statements,
            "current_lines": current_lines,
            "matched_lines": matched_lines,
            "current_snippet": current_snippet,
            "matched_snippet": matched_snippet,
        }
