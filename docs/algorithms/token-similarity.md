# Token Similarity Algorithm Specification

## 1. Input
Two source code files $F_A$ and $F_B$.

## 2. Preprocessing
- Comments removed (`re.sub(r'#.*$', '', line)`).
- Whitespace and formatting normalized (`code_normalizer.py`).

## 3. Tokenization
Extracted language-aware tokens $\mathbf{T}_A$ and $\mathbf{T}_B$ using structural regex pattern `\b[a-zA-Z_]\w*\b|[+\-*/%=<>!&|^~]+`.

## 4. Algorithm & Formula
Jaccard Token Set Similarity:

$$J(\mathbf{T}_A, \mathbf{T}_B) = \frac{|\mathbf{T}_A \cap \mathbf{T}_B|}{|\mathbf{T}_A \cup \mathbf{T}_B|}$$

## 5. Output
Normalized similarity score in range $[0.0, 1.0]$.
- $0.0$: No overlapping tokens.
- $1.0$: Identical normalized token sets.
