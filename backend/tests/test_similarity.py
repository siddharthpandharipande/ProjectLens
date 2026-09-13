import pytest
from app.services.code_normalizer import normalize_source_code, tokenize_code
from app.services.token_similarity import calculate_token_similarity
from app.services.ast_similarity import calculate_ast_similarity
from app.services.semantic_similarity import calculate_semantic_similarity
from app.services.similarity_fusion import fuse_similarity_scores

def test_token_similarity_identical():
    code_a = "def process(data):\n    return data * 2\n"
    code_b = "def process(data):\n    return data * 2\n"
    res = calculate_token_similarity(code_a, code_b)
    assert res["score"] == 1.0

def test_ast_similarity():
    code_a = "def process(data):\n    if data:\n        return True\n"
    code_b = "def execute(val):\n    if val:\n        return True\n"
    res = calculate_ast_similarity(code_a, code_b)
    assert res["score"] > 0.80

def test_similarity_fusion():
    fusion = fuse_similarity_scores(1.0, 0.9, 0.8)
    assert fusion["overall_similarity"] > 0.85
    assert fusion["confidence"] == "HIGH"
