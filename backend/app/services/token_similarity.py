from typing import Dict, Any
from app.services.code_normalizer import normalize_source_code, tokenize_code

def compute_jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    """
    Computes Jaccard Similarity J(A,B) = |A ∩ B| / |A ∪ B|.
    """
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))

    if union == 0:
        return 0.0

    return round(float(intersection / union), 4)

def calculate_token_similarity(code_a: str, code_b: str, language: str = "Python") -> Dict[str, Any]:
    """
    Normalizes both source contents, extracts tokens, and returns token similarity score.
    """
    norm_a = normalize_source_code(code_a, language)
    norm_b = normalize_source_code(code_b, language)

    tokens_a = tokenize_code(norm_a)
    tokens_b = tokenize_code(norm_b)

    score = compute_jaccard_similarity(tokens_a, tokens_b)

    return {
        "algorithm": "JACCARD_TOKEN_SIMILARITY",
        "score": score,
        "token_count_a": len(tokens_a),
        "token_count_b": len(tokens_b),
        "common_tokens": list(tokens_a.intersection(tokens_b))[:15],
    }
