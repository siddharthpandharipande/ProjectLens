# AST Structural Similarity Algorithm Specification

## 1. Input
Two Python source code contents $C_A$ and $C_B$.

## 2. Preprocessing
Parses contents into Abstract Syntax Trees $\text{AST}(A)$ and $\text{AST}(B)$ via Python `ast` module.

## 3. Node Vector Construction
Traverses AST nodes using `ast.walk` and computes node frequency vectors $\mathbf{V}_A$ and $\mathbf{V}_B$ across AST node types (`FunctionDef`, `ClassDef`, `For`, `If`, `BinOp`, etc.).

## 4. Formula
Cosine Similarity over AST Node Frequency Vectors:

$$\text{Sim}_{\text{AST}} = \frac{\mathbf{V}_A \cdot \mathbf{V}_B}{\|\mathbf{V}_A\| \|\mathbf{V}_B\|} = \frac{\sum_k V_A(k) V_B(k)}{\sqrt{\sum_k V_A(k)^2} \sqrt{\sum_k V_B(k)^2}}$$

## 5. Output
Structural AST similarity score in range $[0.0, 1.0]$, ignoring variable renaming and comment differences.
