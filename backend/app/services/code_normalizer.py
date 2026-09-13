import re

def normalize_source_code(content: str, language: str = "Python") -> str:
    """
    Normalizes source code prior to comparison:
    - Removes comments
    - Strips excess whitespace and formatting
    - Standardizes indentation
    """
    if not content:
        return ""

    lines = content.splitlines()
    clean_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if language == "Python":
            if stripped.startswith("#"):
                continue
            # Remove inline comments
            line_no_comment = re.sub(r'#.*$', '', line)
        else:
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue
            line_no_comment = re.sub(r'//.*$', '', line)

        clean = line_no_comment.strip()
        if clean:
            clean_lines.append(clean)

    return "\n".join(clean_lines)

def tokenize_code(content: str) -> set:
    """
    Tokenizes normalized source code into set of structural tokens.
    """
    tokens = re.findall(r'\b[a-zA-Z_]\w*\b|[+\-*/%=<>!&|^~]+', content)
    return set(tokens)
