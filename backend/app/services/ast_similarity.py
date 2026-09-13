import ast
from typing import Dict, Any, List
from collections import Counter

def extract_ast_node_types(content: str) -> List[str]:
    """
    Parses Python source content and returns list of AST node type names.
    """
    try:
        tree = ast.parse(content)
        return [type(node).__name__ for node in ast.walk(tree)]
    except Exception:
        return []

def calculate_ast_similarity(code_a: str, code_b: str) -> Dict[str, Any]:
    """
    Computes structural AST node frequency similarity between Python source files.
    """
    nodes_a = extract_ast_node_types(code_a)
    nodes_b = extract_ast_node_types(code_b)

    if not nodes_a or not nodes_b:
        return {
            "algorithm": "AST_NODE_FREQUENCY",
            "score": 0.0,
            "matched_nodes": 0,
        }

    counts_a = Counter(nodes_a)
    counts_b = Counter(nodes_b)

    all_keys = set(counts_a.keys()).union(set(counts_b.keys()))
    
    # Cosine similarity over AST node frequency vectors
    dot_product = sum(counts_a[k] * counts_b[k] for k in all_keys)
    mag_a = (sum(counts_a[k] ** 2 for k in all_keys)) ** 0.5
    mag_b = (sum(counts_b[k] ** 2 for k in all_keys)) ** 0.5

    if mag_a == 0 or mag_b == 0:
        score = 0.0
    else:
        score = round(float(dot_product / (mag_a * mag_b)), 4)

    return {
        "algorithm": "AST_NODE_FREQUENCY",
        "score": score,
        "nodes_a_count": len(nodes_a),
        "nodes_b_count": len(nodes_b),
    }
