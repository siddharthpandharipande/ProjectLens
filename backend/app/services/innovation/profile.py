"""Profile representation for Phase 7B Innovation Analyzer.

Defines the structured data models representing a project's problem statement,
target users, proposed solution, features with implementation evidence classification,
technology stack, architecture, and claimed contributions.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional


class EvidenceType(StrEnum):
    """Classification of evidence backing a project feature or claim."""

    VERIFIED_MATCH = "verified_match"  # Mentioned in docs AND found in code
    DOCUMENTED_FEATURE = "documented_feature"  # Mentioned in docs with partial code hint
    DETECTED_IMPLEMENTATION = "detected_implementation"  # Found in code, not in docs
    UNVERIFIED_CLAIM = "unverified_claim"  # Documented, but missing code implementation
    INSUFFICIENT_INFORMATION = "insufficient_information"  # Insufficient data to verify


@dataclass
class FeatureEvidence:
    """An individual feature and its implementation evidence status."""

    name: str
    description: str = ""
    evidence_type: str = EvidenceType.INSUFFICIENT_INFORMATION
    doc_reference: Optional[str] = None
    code_reference: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "evidence_type": str(self.evidence_type),
            "doc_reference": self.doc_reference,
            "code_reference": self.code_reference,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureEvidence":
        return cls(
            name=data.get("name", "Unnamed Feature"),
            description=data.get("description", ""),
            evidence_type=data.get("evidence_type", EvidenceType.INSUFFICIENT_INFORMATION),
            doc_reference=data.get("doc_reference"),
            code_reference=data.get("code_reference"),
        )


@dataclass
class ProjectProfile:
    """Normalized structured innovation profile of a project."""

    project_id: str
    title: str = ""
    problem_statement: str = ""
    domain: str = "General Software"
    target_users: List[str] = field(default_factory=list)
    proposed_solution: str = ""
    features: List[FeatureEvidence] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    algorithms: List[str] = field(default_factory=list)
    frontend_components: List[str] = field(default_factory=list)
    backend_components: List[str] = field(default_factory=list)
    database_structure: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    claimed_contributions: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    verification_needed: List[str] = field(default_factory=list)
    has_documentation: bool = False
    is_empty: bool = False
    is_sufficient: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_statement": self.problem_statement,
            "domain": self.domain,
            "target_users": self.target_users,
            "proposed_solution": self.proposed_solution,
            "features": [f.to_dict() for f in self.features],
            "technology_stack": {
                "languages": self.languages,
                "frameworks": self.frameworks,
                "libraries": self.libraries,
                "databases": self.databases,
                "algorithms": self.algorithms,
            },
            "architecture": {
                "frontend_components": self.frontend_components,
                "backend_components": self.backend_components,
                "database_structure": self.database_structure,
                "modules": self.modules,
            },
            "claimed_contribution": {
                "claims": self.claimed_contributions,
                "supporting_evidence": self.supporting_evidence,
                "verification_needed": self.verification_needed,
            },
            "has_documentation": self.has_documentation,
            "is_empty": self.is_empty,
            "is_sufficient": self.is_sufficient,
        }

    @classmethod
    def from_dict(cls, project_id: str, data: Dict[str, Any], title: str = "") -> "ProjectProfile":
        tech = data.get("technology_stack", {})
        arch = data.get("architecture", {})
        claim = data.get("claimed_contribution", {})
        features_data = data.get("features", [])

        features = [
            FeatureEvidence.from_dict(f) if isinstance(f, dict) else f
            for f in features_data
        ]

        return cls(
            project_id=project_id,
            title=title,
            problem_statement=data.get("problem_statement", ""),
            domain=data.get("domain", "General Software"),
            target_users=data.get("target_users", []),
            proposed_solution=data.get("proposed_solution", ""),
            features=features,
            languages=tech.get("languages", []),
            frameworks=tech.get("frameworks", []),
            libraries=tech.get("libraries", []),
            databases=tech.get("databases", []),
            algorithms=tech.get("algorithms", []),
            frontend_components=arch.get("frontend_components", []),
            backend_components=arch.get("backend_components", []),
            database_structure=arch.get("database_structure", []),
            modules=arch.get("modules", []),
            claimed_contributions=claim.get("claims", []),
            supporting_evidence=claim.get("supporting_evidence", []),
            verification_needed=claim.get("verification_needed", []),
            has_documentation=data.get("has_documentation", False),
            is_empty=data.get("is_empty", False),
            is_sufficient=data.get("is_sufficient", True),
        )

    def get_composite_text(self) -> str:
        """Render a unified textual summary for TF-IDF / vector embedding."""
        parts: List[str] = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.domain:
            parts.append(f"Domain: {self.domain}")
        if self.problem_statement:
            parts.append(f"Problem: {self.problem_statement}")
        if self.proposed_solution:
            parts.append(f"Solution: {self.proposed_solution}")
        if self.features:
            feature_names = [f.name for f in self.features]
            parts.append(f"Features: {', '.join(feature_names)}")
        all_tech = self.languages + self.frameworks + self.libraries + self.databases
        if all_tech:
            parts.append(f"Technologies: {', '.join(all_tech)}")
        if self.algorithms:
            parts.append(f"Algorithms: {', '.join(self.algorithms)}")
        if self.claimed_contributions:
            parts.append(f"Contributions: {', '.join(self.claimed_contributions)}")
        return "\n".join(parts)

