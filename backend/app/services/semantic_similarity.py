import math
from typing import Dict, Any, List
from collections import Counter
from app.services.code_normalizer import normalize_source_code, tokenize_code

def calculate_semantic_similarity(code_a: str, code_b: str, language: str = "Python") -> Dict[str, Any]:
    """
    Computes semantic similarity using TF-IDF token vector embeddings and Cosine Similarity.
    """
    norm_a = normalize_source_code(code_a, language)
    norm_b = normalize_source_code(code_b, language)

    tokens_a = list(tokenize_code(norm_a))
    tokens_b = list(tokenize_code(norm_b))

    if not tokens_a or not tokens_b:
        return {"algorithm": "COSINE_TOKEN_EMBEDDING", "score": 0.0}

    freq_a = Counter(tokens_a)
    freq_b = Counter(tokens_b)

    all_vocab = set(freq_a.keys()).union(set(freq_b.keys()))

    dot_product = sum(freq_a[word] * freq_b[word] for word in all_vocab)
    mag_a = math.sqrt(sum(val ** 2 for val in freq_a.values()))
    mag_b = math.sqrt(sum(val ** 2 for val in freq_b.values()))

    if mag_a == 0 or mag_b == 0:
        score = 0.0
    else:
        score = round(float(dot_product / (mag_a * mag_b)), 4)

    return {
        "algorithm": "COSINE_TOKEN_EMBEDDING",
        "score": score,
        "vocab_size": len(all_vocab),
    }
