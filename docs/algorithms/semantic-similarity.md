# Semantic Similarity Algorithm Specification

## 1. Input
Normalized source code chunks across compared projects.

## 2. Preprocessing & Embedding
- Source code is chunked into logical units (files / classes / functions).
- Embedded into high-dimensional vector representations using TF-IDF token frequency distributions and code embeddings.

## 3. Formula
Cosine Similarity over Token Vectors:

$$\text{Sim}_{\text{semantic}} = \frac{\mathbf{E}_A \cdot \mathbf{E}_B}{\|\mathbf{E}_A\| \|\mathbf{E}_B\|}$$

## 4. Output
Semantic similarity score in range $[0.0, 1.0]$.
