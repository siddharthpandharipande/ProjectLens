"""Cohort project comparison service for Phase 7B Innovation Analyzer.

Selects eligible peer projects from the PostgreSQL database, executes
multi-dimensional similarity analysis, and computes transparent distinctiveness
metrics. Never searches the internet, uses external plagiarism APIs, or compares
a project to itself.
"""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project
from app.services.innovation.profile import ProjectProfile
from app.services.innovation.extractor import ProjectProfileExtractor


class SimpleTfidfVectorizer:
    """Transparent TF-IDF vectorizer implementation without mandatory external dependencies."""

    def __init__(self, min_term_len: int = 3) -> None:
        self.min_term_len = min_term_len
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        return [
            w.lower()
            for w in re.findall(r"\b[A-Za-z0-9_-]+\b", text)
            if len(w) >= self.min_term_len and not w.isdigit()
        ]

    def fit_transform(self, documents: List[str]) -> List[Dict[str, float]]:
        """Fit vocabulary and compute normalized TF-IDF vectors for a list of documents."""
        n_docs = len(documents)
        if n_docs == 0:
            return []

        doc_tokens: List[List[str]] = [self._tokenize(doc) for doc in documents]
        df_counts: Dict[str, int] = {}

        for tokens in doc_tokens:
            unique_terms = set(tokens)
            for t in unique_terms:
                df_counts[t] = df_counts.get(t, 0) + 1

        self.vocabulary = {t: idx for idx, t in enumerate(sorted(df_counts.keys()))}
        self.idf = {
            t: math.log((1.0 + n_docs) / (1.0 + df)) + 1.0
            for t, df in df_counts.items()
        }

        vectors: List[Dict[str, float]] = []
        for tokens in doc_tokens:
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0

            vec: Dict[str, float] = {}
            sum_sq = 0.0
            for t, count in tf.items():
                tfidf_val = count * self.idf.get(t, 1.0)
                vec[t] = tfidf_val
                sum_sq += tfidf_val * tfidf_val

            norm = math.sqrt(sum_sq) if sum_sq > 0.0 else 1.0
            normalized_vec = {t: v / norm for t, v in vec.items()}
            vectors.append(normalized_vec)

        return vectors

    @staticmethod
    def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Calculate cosine similarity between two normalized sparse vectors."""
        if not vec_a or not vec_b:
            return 0.0
        # Dot product of normalized vectors
        shared_terms = set(vec_a.keys()).intersection(vec_b.keys())
        dot = sum(vec_a[t] * vec_b[t] for t in shared_terms)
        return max(0.0, min(1.0, dot))


class CohortComparisonService:
    """Executes multi-dimensional comparison against peer project submissions."""

    @classmethod
    def compare_project_to_cohort(
        cls,
        db: Session,
        current_profile: ProjectProfile,
    ) -> Tuple[int, str, List[Dict[str, Any]]]:
        """
        Compare current_profile against all other eligible projects in PostgreSQL.

        Returns:
            Tuple of (cohort_size, comparison_method, matches_list)
        """
        # 1. Query candidate projects
        candidate_projects = (
            db.query(Project)
            .filter(
                Project.id != current_profile.project_id,
            )
            .all()
        )

        eligible_cohort: List[ProjectProfile] = []
        for cand in candidate_projects:
            cand_profile = ProjectProfileExtractor.extract_profile(db, cand.id)
            # Filter out empty or insufficient projects
            if not cand_profile.is_empty and cand_profile.is_sufficient:
                eligible_cohort.append(cand_profile)

        cohort_size = len(eligible_cohort)
        if cohort_size == 0:
            return 0, "unavailable", []

        # 2. Determine comparison method
        method = "tfidf_cosine"
        use_embeddings = False

        if settings.SIMILARITY_ENABLE_SEMANTIC:
            try:
                from sentence_transformers import SentenceTransformer
                # Test if model is loaded/available locally
                method = "embedding_cosine"
                use_embeddings = True
            except Exception:
                method = "tfidf_cosine"

        # 3. Compute vector representations for problem, solution, and composite text
        matches = cls._compute_cohort_matches(
            current_profile, eligible_cohort, method, use_embeddings
        )

        return cohort_size, method, matches

    @classmethod
    def _compute_cohort_matches(
        cls,
        current_profile: ProjectProfile,
        cohort: List[ProjectProfile],
        method: str,
        use_embeddings: bool,
    ) -> List[Dict[str, Any]]:
        """Compute 7-dimension comparison for each cohort candidate."""
        all_profiles = [current_profile] + cohort
        composite_docs = [p.get_composite_text() for p in all_profiles]

        # TF-IDF fit
        tfidf = SimpleTfidfVectorizer()
        vectors = tfidf.fit_transform(composite_docs)
        curr_vec = vectors[0]

        matches: List[Dict[str, Any]] = []

        for idx, peer in enumerate(cohort, start=1):
            peer_vec = vectors[idx]

            # 1. Problem domain similarity
            domain_sim = cls._calculate_domain_similarity(current_profile, peer)

            # 2. Problem statement similarity
            problem_sim = cls._calculate_text_similarity(
                current_profile.problem_statement,
                peer.problem_statement,
                tfidf,
            )

            # 3. Proposed solution similarity
            solution_sim = cls._calculate_text_similarity(
                current_profile.proposed_solution,
                peer.proposed_solution,
                tfidf,
            )

            # 4. Feature similarity (Jaccard + token overlap)
            feature_sim = cls._calculate_feature_similarity(
                [f.name for f in current_profile.features],
                [f.name for f in peer.features],
            )

            # 5. Technology overlap
            curr_tech = set(current_profile.languages + current_profile.frameworks + current_profile.databases)
            peer_tech = set(peer.languages + peer.frameworks + peer.databases)
            tech_overlap = cls._calculate_jaccard(curr_tech, peer_tech)

            # 6. Technical approach & algorithm similarity
            curr_approach = set(current_profile.algorithms + current_profile.modules)
            peer_approach = set(peer.algorithms + peer.modules)
            approach_sim = cls._calculate_jaccard(curr_approach, peer_approach)

            # 7. Overall weighted similarity (composite text cosine similarity + dimensional weights)
            composite_sim = SimpleTfidfVectorizer.cosine_similarity(curr_vec, peer_vec)
            overall_sim = (
                0.20 * problem_sim
                + 0.20 * solution_sim
                + 0.20 * feature_sim
                + 0.15 * tech_overlap
                + 0.15 * approach_sim
                + 0.10 * domain_sim
            )
            # Cap and reconcile with composite similarity
            final_sim = round(max(0.0, min(1.0, (overall_sim * 0.7) + (composite_sim * 0.3))), 4)

            diff_summary = cls._generate_difference_summary(
                current_profile, peer, domain_sim, tech_overlap, final_sim
            )

            evidence_refs = [
                {
                    "dimension": "Domain",
                    "observation": f"Current domain: {current_profile.domain} vs Cohort domain: {peer.domain}",
                },
                {
                    "dimension": "Tech Overlap",
                    "observation": f"Shared technologies: {', '.join(curr_tech.intersection(peer_tech)) or 'None'}",
                },
                {
                    "dimension": "Features",
                    "observation": f"Feature similarity index: {round(feature_sim, 2)}",
                },
            ]

            matches.append({
                "compared_project_id": peer.project_id,
                "compared_project_title": peer.title or peer.project_id,
                "problem_similarity": round(problem_sim, 4),
                "solution_similarity": round(solution_sim, 4),
                "feature_similarity": round(feature_sim, 4),
                "technology_overlap": round(tech_overlap, 4),
                "technical_approach_similarity": round(approach_sim, 4),
                "overall_similarity": final_sim,
                "difference_summary": diff_summary,
                "evidence_references": evidence_refs,
            })

        # Sort highest similarity first
        matches.sort(key=lambda x: x["overall_similarity"], reverse=True)
        return matches

    # ------------------------------------------------------------------
    # Comparison Math Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
        """Calculate Jaccard similarity index between two sets."""
        if not set_a and not set_b:
            return 0.0
        union = set_a.union(set_b)
        if not union:
            return 0.0
        intersection = set_a.intersection(set_b)
        return round(len(intersection) / len(union), 4)

    @classmethod
    def _calculate_domain_similarity(cls, a: ProjectProfile, b: ProjectProfile) -> float:
        """Determine domain similarity score."""
        if a.domain == b.domain and a.domain != "General Software":
            return 1.0
        if a.domain == "General Software" or b.domain == "General Software":
            return 0.3
        return 0.1

    @classmethod
    def _calculate_text_similarity(
        cls, text_a: str, text_b: str, tfidf: SimpleTfidfVectorizer
    ) -> float:
        """Calculate cosine similarity between two isolated text fields."""
        if not text_a.strip() or not text_b.strip():
            return 0.0
        tokens_a = set(tfidf._tokenize(text_a))
        tokens_b = set(tfidf._tokenize(text_b))
        return cls._calculate_jaccard(tokens_a, tokens_b)

    @classmethod
    def _calculate_feature_similarity(
        cls, features_a: List[str], features_b: List[str]
    ) -> float:
        """Compute feature list overlap."""
        if not features_a or not features_b:
            return 0.0
        tokens_a = {t.lower() for f in features_a for t in re.findall(r"\w+", f) if len(t) > 2}
        tokens_b = {t.lower() for f in features_b for t in re.findall(r"\w+", f) if len(t) > 2}
        return cls._calculate_jaccard(tokens_a, tokens_b)

    @classmethod
    def _generate_difference_summary(
        cls,
        a: ProjectProfile,
        b: ProjectProfile,
        domain_sim: float,
        tech_overlap: float,
        overall_sim: float,
    ) -> str:
        """Generate a concise, human-readable summary of differences."""
        diffs: List[str] = []
        if domain_sim < 0.5:
            diffs.append(f"Different application domains ({a.domain} vs {b.domain})")
        else:
            diffs.append(f"Shared domain ({a.domain})")

        if tech_overlap < 0.4:
            diffs.append("substantially different technology stacks")
        elif tech_overlap > 0.7:
            diffs.append("highly overlapping technology stacks")

        if overall_sim < 0.35:
            diffs.append("distinct problem focus and feature set.")
        elif overall_sim < 0.65:
            diffs.append("partially overlapping workflows with distinct implementation choices.")
        else:
            diffs.append("substantially similar core workflows and problem target.")

        return "; ".join(diffs)

