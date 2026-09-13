# Score Engine Specification

## 1. Overview
ProjectLens evaluation engine synthesizes 4 key dimensions:
1. **Technical Execution** (Code Quality, AST complexity, LOC metrics, file organization)
2. **Originality** (Similarity Fusion: 20% Token + 50% AST + 30% Semantic)
3. **Documentation Integrity** (Section coverage, clarity, Code ↔ Doc Mismatch findings)
4. **Development Process** (Git commit frequency, timeline span, lines added/deleted)

## 2. Overall Score Calculation
When all 4 dimensions are evaluated:
$$\text{Overall Score} = \frac{S_{\text{tech}} + S_{\text{orig}} + S_{\text{doc}} + S_{\text{dev}}}{4}$$

When Git history or comparison data is absent:
$$\text{Overall Score} = \frac{\sum_{k \in \text{Available}} S_k}{|\text{Available}|}$$

Status string reflects exact dimension count (e.g. "Based on 3 of 4 evaluation dimensions").
