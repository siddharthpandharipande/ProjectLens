# Code Quality Analysis Algorithm Specification

## 1. Input
Raw source code files (`.py`, `.ts`, `.js`, `.java`, `.cpp`, `.go`, etc.) scanned from project directory.

## 2. Preprocessing
- Strips trailing whitespace.
- Classifies lines into executable code, comments, and blank lines.
- Ignores vendor (`node_modules`, `.venv`) and generated directories.

## 3. Parsing & Metrics Extraction
- **Python**: AST parsing (`ast.walk`) + Radon Cyclomatic Complexity (`radon.complexity`).
- **Generic Languages**: Structural pattern signatures (regex matching function/class signatures and decision branch keywords `if`, `else if`, `for`, `while`, `switch`, `case`, `catch`, `&&`, `||`).

## 4. Formula & Scoring
- **Complexity Score**: $S_{\text{comp}} = \max(0, \min(100, 100 - (\bar{C} - 1.0) \times 15))$
- **Weighted Overall Quality**:
  $$S_{\text{quality}} = 0.25 S_{\text{comp}} + 0.25 S_{\text{maint}} + 0.20 S_{\text{mod}} + 0.15 S_{\text{dup}} + 0.15 S_{\text{naming}}$$

## 5. Output
JSON payload containing LOC metrics, cyclomatic complexity averages, structural findings (`HIGH_COMPLEXITY`, `LARGE_FILE`, `LOW_DOCUMENTATION_RATIO`), and normalized score (0–100).
