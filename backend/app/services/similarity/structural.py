"""
structural.py

Hierarchical AST and syntax-tree structural similarity service.

Methodology & Structural Representation:
Instead of treating code as a flat sequence of token types or flat node lists,
this service preserves AST nesting and parent-child relationships:

1. Hierarchical Ancestry Paths (Tree Path Signatures):
   For each statement, declaration, and control-flow block, the service records
   the path from the root or enclosing scope down to the node:
   e.g. "Module/ClassDef/FunctionDef/For/If/Assign".

2. Parent-Child Directed Edges with Depth Bucketing:
   Extracts directed (ParentType, ChildType, DepthTier) tuples capturing local nesting.

3. Structural Subtree Signatures:
   For function/method blocks, loops, and conditional structures, the service builds a
   tuple (NodeType, (ChildType1, ChildType2, ...)) representing exact branch structure.

Supported Languages:
- Python: Uses standard library `ast.parse()` to extract hierarchical AST nodes.
- JavaScript / TypeScript: Uses Tree-sitter grammar to traverse named syntax-tree nodes.
- Java: Uses Tree-sitter grammar to traverse class, method, loop, and statement hierarchies.
- Unsupported Languages: Explicitly reports None without fabricating scores.
"""

import ast
import textwrap
from typing import Set, Tuple, Optional, Dict, Any, List

# Tree-sitter support
try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_java

    JS_LANGUAGE = Language(tree_sitter_javascript.language())
    JAVA_LANGUAGE = Language(tree_sitter_java.language())
    TREESITTER_AVAILABLE = True
except Exception:
    TREESITTER_AVAILABLE = False
    JS_LANGUAGE = None
    JAVA_LANGUAGE = None


class StructuralSimilarityAnalyzer:
    """Computes hierarchical syntax-tree structural similarity between source files."""

    @classmethod
    def get_python_hierarchical_features(cls, code: str) -> Optional[Set[str]]:
        """
        Parses Python code and extracts hierarchical AST features:
        - Ancestry paths (e.g., 'Module/ClassDef/FunctionDef/If')
        - Directed parent-child edges with depth tier
        - Subtree branch signatures
        Returns None if code has syntax errors.
        """
        try:
            tree = ast.parse(textwrap.dedent(code))
        except (SyntaxError, ValueError):
            return None

        features: Set[str] = set()

        def walk_node(node: ast.AST, path: List[str], depth: int):
            node_name = node.__class__.__name__

            # Skip trivial expression leaves to focus on structural architecture
            if node_name in ("Load", "Store", "Del", "Pass"):
                return

            current_path = path + [node_name]
            # Record full ancestry path up to depth 6
            if len(current_path) >= 2:
                features.add("PATH:" + "/".join(current_path[-5:]))

            child_types: List[str] = []
            for child in ast.iter_child_nodes(node):
                c_name = child.__class__.__name__
                if c_name not in ("Load", "Store", "Del"):
                    child_types.append(c_name)
                    # Record parent-child relation with depth bucket
                    depth_tier = min(depth // 2, 4)
                    features.add(f"EDGE:{node_name}->{c_name}@d{depth_tier}")
                    walk_node(child, current_path, depth + 1)

            # Record branch signature for compound blocks
            if child_types and node_name in (
                "FunctionDef",
                "AsyncFunctionDef",
                "ClassDef",
                "If",
                "For",
                "AsyncFor",
                "While",
                "Try",
                "With",
            ):
                sig = f"SUBTREE:{node_name}:" + ",".join(child_types[:8])
                features.add(sig)

        walk_node(tree, [], 0)
        return features

    @classmethod
    def get_treesitter_hierarchical_features(
        cls, code: str, language: str
    ) -> Optional[Set[str]]:
        """
        Parses JavaScript, TypeScript, or Java code via Tree-sitter and extracts
        hierarchical syntax-tree paths and parent-child edges.
        """
        if not TREESITTER_AVAILABLE:
            return None

        lang = language.lower()
        parser = Parser()

        if lang in ("javascript", "typescript", "jsx", "tsx"):
            if not JS_LANGUAGE:
                return None
            parser.language = JS_LANGUAGE
        elif lang == "java":
            if not JAVA_LANGUAGE:
                return None
            parser.language = JAVA_LANGUAGE
        else:
            return None

        try:
            tree = parser.parse(bytes(code, "utf-8"))
            if tree.root_node.has_error:
                # Syntax or parse error detected, but proceed with partial tree if possible
                pass
        except Exception:
            return None

        features: Set[str] = set()

        def walk_ts(node, path: List[str], depth: int):
            if not node.is_named:
                return

            node_type = node.type
            current_path = path + [node_type]

            if len(current_path) >= 2:
                features.add("PATH:" + "/".join(current_path[-5:]))

            child_types: List[str] = []
            for child in node.children:
                if child.is_named:
                    c_type = child.type
                    child_types.append(c_type)
                    depth_tier = min(depth // 2, 4)
                    features.add(f"EDGE:{node_type}->{c_type}@d{depth_tier}")
                    walk_ts(child, current_path, depth + 1)

            if child_types and any(
                k in node_type
                for k in (
                    "function",
                    "method",
                    "class",
                    "if",
                    "for",
                    "while",
                    "try",
                    "switch",
                )
            ):
                sig = f"SUBTREE:{node_type}:" + ",".join(child_types[:8])
                features.add(sig)

        walk_ts(tree.root_node, [], 0)
        return features

    @classmethod
    def extract_features(
        cls, code: str, language: Optional[str]
    ) -> Tuple[Optional[Set[str]], bool, Optional[str]]:
        """
        Extract hierarchical structural features for the given code and language.
        Returns:
            Tuple of (features_set, is_supported, error_message)
        """
        lang = (language or "").lower()

        if lang == "python":
            features = cls.get_python_hierarchical_features(code)
            if features is None:
                return None, True, "Python AST parse error (syntax error in source code)"
            return features, True, None

        elif lang in ("javascript", "typescript", "jsx", "tsx", "java"):
            features = cls.get_treesitter_hierarchical_features(code, lang)
            if features is None:
                return (
                    None,
                    True,
                    f"Tree-sitter parser failed or syntax error for {language}",
                )
            return features, True, None

        # Unsupported for AST
        return (
            None,
            False,
            f"Language '{language}' does not have a supported structural AST parser in ProjectLens",
        )

    @classmethod
    def calculate_structural_similarity(
        cls,
        code_a: str,
        code_b: str,
        lang_a: Optional[str] = None,
        lang_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute hierarchical structural similarity score between two source files.
        Returns:
            dict containing:
            - structural_similarity (float or None)
            - is_supported (bool)
            - method_used (str)
            - error (str or None)
        """
        # If languages are incompatible (e.g. Python vs Java), cannot compare AST directly
        if (lang_a or "").lower() != (lang_b or "").lower():
            return {
                "structural_similarity": None,
                "is_supported": False,
                "method_used": "none",
                "error": f"Incompatible languages for AST comparison ({lang_a} vs {lang_b})",
            }

        feats_a, sup_a, err_a = cls.extract_features(code_a, lang_a)
        feats_b, sup_b, err_b = cls.extract_features(code_b, lang_b)

        if not sup_a or not sup_b:
            return {
                "structural_similarity": None,
                "is_supported": False,
                "method_used": "none",
                "error": err_a or err_b,
            }

        if feats_a is None or feats_b is None:
            return {
                "structural_similarity": None,
                "is_supported": True,
                "method_used": "ast_hierarchical",
                "error": err_a or err_b,
            }

        # Both parsed successfully!
        if not feats_a or not feats_b:
            # Empty files have no structural features
            return {
                "structural_similarity": 0.0,
                "is_supported": True,
                "method_used": "ast_hierarchical",
                "error": None,
            }

        # Jaccard on hierarchical features
        intersection = feats_a.intersection(feats_b)
        union = feats_a.union(feats_b)
        jaccard = (len(intersection) / len(union)) if union else 0.0

        return {
            "structural_similarity": round(jaccard * 100.0, 1),
            "is_supported": True,
            "method_used": "ast_hierarchical",
            "error": None,
        }
