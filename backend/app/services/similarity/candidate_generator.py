"""
candidate_generator.py

Candidate generation and comparison filtering service.
Limits computationally expensive comparisons by filtering on:
- Database cohort projects (excludes self-comparison, requires extracted source files)
- Compatible programming languages
- Minimum content length (skips empty or 1-2 line boilerplate)
- Exact SHA-256 content hashes (instant exact match detection)
"""

import hashlib
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectFile


class CandidateGenerator:
    """Generates and prefilters candidate project and file pairs for comparison."""

    # Language compatibility matrix: defines which languages can be meaningfully compared
    COMPATIBLE_LANGUAGES = {
        "python": {"python"},
        "javascript": {"javascript", "typescript", "jsx", "tsx"},
        "typescript": {"javascript", "typescript", "jsx", "tsx"},
        "jsx": {"javascript", "typescript", "jsx", "tsx"},
        "tsx": {"javascript", "typescript", "jsx", "tsx"},
        "java": {"java"},
        "c": {"c", "cpp"},
        "cpp": {"c", "cpp"},
        "c++": {"c", "cpp"},
    }

    @classmethod
    def get_eligible_cohort_projects(
        cls, db: Session, current_project_id: str
    ) -> List[Project]:
        """
        Query all other projects in the database that are eligible for comparison:
        - Excludes self-comparison (Project.id != current_project_id)
        - Must have at least one indexed source code file
        """
        other_projects = (
            db.query(Project)
            .filter(Project.id != current_project_id)
            .order_by(Project.created_at.desc())
            .all()
        )

        eligible: List[Project] = []
        for p in other_projects:
            has_source = (
                db.query(ProjectFile.id)
                .filter(
                    ProjectFile.project_id == p.id,
                    ProjectFile.category == "Source Code",
                )
                .first()
            )
            if has_source:
                eligible.append(p)

        return eligible

    @classmethod
    def are_languages_compatible(cls, lang_a: Optional[str], lang_b: Optional[str]) -> bool:
        """Check if two programming languages are compatible for cross-comparison."""
        if not lang_a or not lang_b:
            return False
        la = lang_a.strip().lower()
        lb = lang_b.strip().lower()
        if la == lb:
            return True
        return lb in cls.COMPATIBLE_LANGUAGES.get(la, set())

    @staticmethod
    def compute_sha256(content: str) -> str:
        """Calculate SHA-256 hash of normalized code content."""
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    @classmethod
    def prefilter_file_pair(
        cls,
        path_a: str,
        code_a: str,
        lang_a: Optional[str],
        path_b: str,
        code_b: str,
        lang_b: Optional[str],
    ) -> Tuple[bool, bool, str]:
        """
        Quick prefilter check on a pair of files:
        Returns:
            Tuple of:
            - is_candidate (bool)
            - is_exact_match (bool)
            - reason (str)
        """
        # 1. Check language compatibility
        if not cls.are_languages_compatible(lang_a, lang_b):
            return False, False, f"Incompatible languages ({lang_a} vs {lang_b})"

        # 2. Check length thresholds (skip trivially empty files)
        if len(code_a.strip()) < 20 or len(code_b.strip()) < 20:
            return False, False, "One or both files are trivially short (< 20 characters)"

        # 3. Check exact SHA-256 content match
        hash_a = cls.compute_sha256(code_a)
        hash_b = cls.compute_sha256(code_b)

        if hash_a == hash_b:
            return True, True, "Exact cryptographic SHA-256 content match"

        return True, False, "Compatible candidate for token and structural analysis"
