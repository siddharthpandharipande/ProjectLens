"""
semantic.py

Optional, locally configurable semantic code similarity service.

Design & Safety Constraints:
- Kept optional and locally configurable via environment variables.
- Does NOT download model weights automatically.
- Treats `all-MiniLM-L6-v2` as an experimental general-purpose embedding baseline,
  not a scientifically validated code-similarity model.
- If disabled or if local weights/dependencies are unavailable, explicitly marks
  semantic similarity as unavailable so the scoring engine can re-normalize weights.
- Never fabricates or synthesizes semantic scores.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings

# Optional dependency imports
_SENTENCE_TRANSFORMER_MODEL = None
_MODEL_INIT_ATTEMPTED = False
_MODEL_INIT_ERROR: Optional[str] = None


class SemanticSimilarityService:
    """Computes semantic embedding similarity between code chunks using a local model."""

    @classmethod
    def initialize_model(cls) -> Tuple[bool, Optional[str]]:
        """
        Attempts to load local sentence-transformers model without auto-downloading.
        Returns (is_ready, error_message).
        """
        global _SENTENCE_TRANSFORMER_MODEL, _MODEL_INIT_ATTEMPTED, _MODEL_INIT_ERROR

        if not settings.SIMILARITY_ENABLE_SEMANTIC:
            return False, "Semantic similarity is disabled in settings (SIMILARITY_ENABLE_SEMANTIC=False) to prevent unexpected downloads."

        if _MODEL_INIT_ATTEMPTED:
            return (_SENTENCE_TRANSFORMER_MODEL is not None), _MODEL_INIT_ERROR

        _MODEL_INIT_ATTEMPTED = True

        try:
            from sentence_transformers import SentenceTransformer
            # Only load if a local path is provided or local files exist
            model_target = settings.SIMILARITY_MODEL_PATH or settings.SIMILARITY_EMBEDDING_MODEL
            # To avoid unexpected network download, if local path is specified we load from path
            _SENTENCE_TRANSFORMER_MODEL = SentenceTransformer(model_target, local_files_only=True)
            _MODEL_INIT_ERROR = None
            return True, None
        except Exception as e:
            _SENTENCE_TRANSFORMER_MODEL = None
            _MODEL_INIT_ERROR = (
                f"Local embedding model unavailable: {str(e)}. "
                "Semantic similarity will be marked unavailable and remaining weights will be re-normalized."
            )
            return False, _MODEL_INIT_ERROR

    @classmethod
    def chunk_source_code(cls, code: str, max_lines: int = 40) -> List[str]:
        """
        Split large source files into manageable code chunks (e.g. functions or 40-line blocks)
        rather than passing entire large repositories as a single text blob.
        """
        lines = code.splitlines()
        if len(lines) <= max_lines:
            return [code.strip()] if code.strip() else []

        chunks: List[str] = []
        step = max(max_lines - 10, 20)  # 10-line overlap
        for i in range(0, len(lines), step):
            chunk_slice = lines[i : i + max_lines]
            chunk_text = "\n".join(chunk_slice).strip()
            if len(chunk_text) > 30:
                chunks.append(chunk_text)
        return chunks or [code.strip()]

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate standard cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))

    @classmethod
    def calculate_semantic_similarity(
        cls,
        code_a: str,
        code_b: str,
    ) -> Dict[str, Any]:
        """
        Compute cosine similarity between embeddings of source code chunks.
        Returns dict containing:
        - semantic_similarity (float or None)
        - is_available (bool)
        - model_name (str)
        - error (str or None)
        """
        is_ready, err = cls.initialize_model()
        model_name = settings.SIMILARITY_EMBEDDING_MODEL

        if not is_ready:
            return {
                "semantic_similarity": None,
                "is_available": False,
                "model_name": model_name,
                "error": err,
            }

        chunks_a = cls.chunk_source_code(code_a)
        chunks_b = cls.chunk_source_code(code_b)

        if not chunks_a or not chunks_b:
            return {
                "semantic_similarity": 0.0,
                "is_available": True,
                "model_name": model_name,
                "error": None,
            }

        try:
            embeddings_a = _SENTENCE_TRANSFORMER_MODEL.encode(chunks_a)
            embeddings_b = _SENTENCE_TRANSFORMER_MODEL.encode(chunks_b)

            max_sim = 0.0
            for emb_a in embeddings_a:
                for emb_b in embeddings_b:
                    sim = cls.cosine_similarity(emb_a.tolist(), emb_b.tolist())
                    if sim > max_sim:
                        max_sim = sim

            return {
                "semantic_similarity": round(max_sim * 100.0, 1),
                "is_available": True,
                "model_name": model_name,
                "error": None,
            }
        except Exception as e:
            return {
                "semantic_similarity": None,
                "is_available": False,
                "model_name": model_name,
                "error": f"Embedding generation failed: {str(e)}",
            }
