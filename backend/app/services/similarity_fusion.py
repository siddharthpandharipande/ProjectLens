from typing import Dict, Any

def fuse_similarity_scores(
    token_score: float,
    ast_score: float,
    semantic_score: float,
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Fuses Token (20%), AST (50%), and Semantic (30%) similarities into normalized Overall Similarity Score.
    """
    if weights is None:
        weights = {"token": 0.20, "ast": 0.50, "semantic": 0.30}

    overall = round(
        (token_score * weights["token"]) +
        (ast_score * weights["ast"]) +
        (semantic_score * weights["semantic"]),
        4
    )

    if overall >= 0.85:
        confidence = "HIGH"
    elif overall >= 0.60:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "token_similarity": round(token_score, 4),
        "ast_similarity": round(ast_score, 4),
        "semantic_similarity": round(semantic_score, 4),
        "overall_similarity": overall,
        "similarity_percentage": round(overall * 100, 1),
        "confidence": confidence,
        "weights": weights,
    }
