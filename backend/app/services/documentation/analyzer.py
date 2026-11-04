import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

from app.services.documentation.extractor import ExtractedDocument, DocumentSection
from app.schemas.documentation import (
    SectionCoverageItem,
    DocumentationQualityMetrics,
    DocumentationScoreFactor,
)


@dataclass
class SectionDefinition:
    key: str
    display_name: str
    is_required: bool
    patterns: List[str]


SECTION_DEFINITIONS: List[SectionDefinition] = [
    SectionDefinition(
        key="abstract",
        display_name="Abstract / Summary",
        is_required=False,
        patterns=[
            r"^abstract\b",
            r"^executive\s+summary\b",
            r"^project\s+summary\b",
            r"^synopsis\b",
        ],
    ),
    SectionDefinition(
        key="introduction",
        display_name="Introduction / Problem Statement",
        is_required=True,
        patterns=[
            r"^introduction\b",
            r"^problem\s+statement\b",
            r"^background\b",
            r"^motivation\b",
            r"^problem\s+definition\b",
            r"^project\s+overview\b",
            r"^about\s+the\s+project\b",
        ],
    ),
    SectionDefinition(
        key="objectives",
        display_name="Objectives / Project Goals",
        is_required=False,
        patterns=[
            r"^objectives?\b",
            r"^project\s+goals?\b",
            r"^aims?\b",
            r"^scope\b",
            r"^project\s+scope\b",
        ],
    ),
    SectionDefinition(
        key="requirements",
        display_name="Requirements / Specifications (SRS)",
        is_required=False,
        patterns=[
            r"^requirements?\b",
            r"^software\s+requirements?\b",
            r"^functional\s+requirements?\b",
            r"^non-?functional\s+requirements?\b",
            r"^system\s+requirements?\b",
            r"^srs\b",
            r"^prerequisites?\b",
            r"^specifications?\b",
        ],
    ),
    SectionDefinition(
        key="setup",
        display_name="Setup / Installation / Usage",
        is_required=True,
        patterns=[
            r"^setup\b",
            r"^installation\b",
            r"^getting\s+started\b",
            r"^how\s+to\s+run\b",
            r"^how\s+to\s+use\b",
            r"^quick\s*start\b",
            r"^usage\b",
            r"^deployment\b",
            r"^running\s+the\s+project\b",
            r"^build\s+instructions?\b",
            r"^execution\b",
        ],
    ),
    SectionDefinition(
        key="methodology",
        display_name="Methodology / Proposed Approach",
        is_required=False,
        patterns=[
            r"^methodology\b",
            r"^proposed\s+methodology\b",
            r"^proposed\s+approach\b",
            r"^system\s+approach\b",
            r"^workflow\b",
            r"^algorithm\s+design\b",
        ],
    ),
    SectionDefinition(
        key="architecture",
        display_name="Architecture & System Design",
        is_required=True,
        patterns=[
            r"^architecture\b",
            r"^system\s+architecture\b",
            r"^system\s+design\b",
            r"^design\b",
            r"^component\s+design\b",
            r"^database\s+design\b",
            r"^data\s+flow\b",
            r"^er\s+diagram\b",
            r"^class\s+diagram\b",
            r"^system\s+components?\b",
        ],
    ),
    SectionDefinition(
        key="implementation",
        display_name="Implementation / Technology Stack",
        is_required=True,
        patterns=[
            r"^implementation\b",
            r"^technology\s+stack\b",
            r"^tech\s+stack\b",
            r"^tools\s+and\s+technologies\b",
            r"^technologies\s+used\b",
            r"^development\s+details?\b",
            r"^modules\b",
            r"^system\s+modules?\b",
        ],
    ),
    SectionDefinition(
        key="testing",
        display_name="Testing, Verification & Results",
        is_required=True,
        patterns=[
            r"^testing\b",
            r"^test\s+results?\b",
            r"^testing\s+and\s+results?\b",
            r"^evaluation\b",
            r"^validation\b",
            r"^test\s+cases?\b",
            r"^unit\s+testing\b",
            r"^experimental\s+results?\b",
            r"^performance\s+analysis\b",
        ],
    ),
    SectionDefinition(
        key="conclusion",
        display_name="Conclusion & Future Work",
        is_required=False,
        patterns=[
            r"^conclusions?\b",
            r"^future\s+work\b",
            r"^future\s+scope\b",
            r"^summary\s+and\s+conclusions?\b",
            r"^limitations?\b",
        ],
    ),
    SectionDefinition(
        key="references",
        display_name="References & Citations",
        is_required=False,
        patterns=[
            r"^references?\b",
            r"^bibliography\b",
            r"^citations?\b",
            r"^works\s+cited\b",
        ],
    ),
]


class DocumentationAnalyzer:
    """
    Deterministic analyzer that recognizes standard report and project sections,
    calculates transparent quality metrics, identifies specific documentation issues,
    and produces a preliminary Documentation Quality Score with factor explanations.
    """

    @classmethod
    def match_heading_to_section(cls, heading: str) -> Optional[str]:
        """
        Maps a heading title to a recognized section key using regex patterns.
        Ignores leading numbers like "1.", "1.2", "Section 3:".
        """
        clean = re.sub(r"^(?:Section\s+)?(?:\d+(?:\.\d+)*[:\-\.]?\s*)", "", heading.strip(), flags=re.IGNORECASE)
        clean = clean.strip().lower()

        for sec in SECTION_DEFINITIONS:
            for pattern in sec.patterns:
                if re.search(pattern, clean, re.IGNORECASE):
                    return sec.key

        return None

    @classmethod
    def analyze_documents(
        cls,
        documents: List[ExtractedDocument],
    ) -> Tuple[
        DocumentationQualityMetrics,
        List[SectionCoverageItem],
        Optional[float],
        Dict[str, Any],
        List[Dict[str, Any]],
        List[str],
    ]:
        """
        Performs full documentation analysis across extracted documents.
        Returns:
            - metrics: DocumentationQualityMetrics
            - section_coverage: List[SectionCoverageItem]
            - preliminary_score: Optional[float]
            - score_explanation: Dict[str, Any]
            - quality_findings: List[Dict[str, Any]]
            - warnings: List[str]
        """
        total_docs = len(documents)
        total_words = sum(d.word_count for d in documents)
        pdf_pages = sum(d.page_count for d in documents if d.file_format == "pdf")

        # Track recognized sections
        section_matches: Dict[str, Dict[str, Any]] = {
            sec.key: {
                "display_name": sec.display_name,
                "is_required": sec.is_required,
                "present": False,
                "headings": set(),
                "files": set(),
            }
            for sec in SECTION_DEFINITIONS
        }

        has_readme = False
        repetition_warnings: List[str] = []
        all_warnings: List[str] = []

        seen_section_contents: Dict[str, str] = {}

        for doc in documents:
            if "readme" in doc.filename.lower():
                has_readme = True

            if doc.warning:
                all_warnings.append(f"{doc.relative_path}: {doc.warning}")

            # Check headings and sections
            for sec in doc.sections:
                sec_key = cls.match_heading_to_section(sec.heading)
                if sec_key:
                    section_matches[sec_key]["present"] = True
                    section_matches[sec_key]["headings"].add(sec.heading)
                    section_matches[sec_key]["files"].add(doc.relative_path)

                # Repetition check on non-trivial section bodies (> 100 chars)
                body_norm = " ".join(sec.content.lower().split())
                if len(body_norm) > 150:
                    body_hash = body_norm[:200]
                    if body_hash in seen_section_contents:
                        prior = seen_section_contents[body_hash]
                        rep_msg = f"Repeated content detected between '{prior}' and '{doc.relative_path} ({sec.heading})'."
                        if rep_msg not in repetition_warnings:
                            repetition_warnings.append(rep_msg)
                    else:
                        seen_section_contents[body_hash] = f"{doc.relative_path} ({sec.heading})"

            # Also check document headings directly if sections were sparse
            for h in doc.headings:
                sec_key = cls.match_heading_to_section(h)
                if sec_key:
                    section_matches[sec_key]["present"] = True
                    section_matches[sec_key]["headings"].add(h)
                    section_matches[sec_key]["files"].add(doc.relative_path)

            # Fallback heuristic: check if setup or testing commands appear in text even without explicit header
            if not section_matches["setup"]["present"]:
                if re.search(r"(?:npm\s+install|pip\s+install|python\s+main|yarn\s+install|docker-compose\s+up|docker\s+run)", doc.text, re.IGNORECASE):
                    section_matches["setup"]["present"] = True
                    section_matches["setup"]["headings"].add("Implicit CLI Commands")
                    section_matches["setup"]["files"].add(doc.relative_path)

            if not section_matches["testing"]["present"]:
                if re.search(r"(?:pytest|npm\s+test|unit\s+tests?|test\s+cases?|test\s+results?)\b", doc.text, re.IGNORECASE):
                    # Only match if there are actual test discussion sentences, not just an isolated token
                    if len(re.findall(r"(?:test|testing|assert|validation)", doc.text, re.IGNORECASE)) >= 3:
                        section_matches["testing"]["present"] = True
                        section_matches["testing"]["headings"].add("Implicit Testing Mentions")
                        section_matches["testing"]["files"].add(doc.relative_path)

        # Build SectionCoverageItems
        coverage_items: List[SectionCoverageItem] = []
        recognized_count = 0
        required_present = 0
        required_total = sum(1 for sec in SECTION_DEFINITIONS if sec.is_required)

        for sec in SECTION_DEFINITIONS:
            data = section_matches[sec.key]
            is_pres = data["present"]
            if is_pres:
                recognized_count += 1
                if sec.is_required:
                    required_present += 1

            coverage_items.append(
                SectionCoverageItem(
                    sectionKey=sec.key,
                    displayName=sec.display_name,
                    isRequired=sec.is_required,
                    isPresent=is_pres,
                    detectedHeadings=sorted(list(data["headings"])),
                    foundInFiles=sorted(list(data["files"])),
                )
            )

        # Has setup & testing
        has_setup = section_matches["setup"]["present"]
        has_testing = section_matches["testing"]["present"]

        metrics = DocumentationQualityMetrics(
            totalDocuments=total_docs,
            totalWords=total_words,
            recognizedSectionsCount=recognized_count,
            requiredSectionsPresent=required_present,
            requiredSectionsTotal=required_total,
            hasReadme=has_readme,
            hasSetupInstructions=has_setup,
            hasTestingSection=has_testing,
            pdfPagesExtracted=pdf_pages,
            repetitionWarnings=repetition_warnings,
        )

        # Generate findings for specific documentation issues
        findings: List[Dict[str, Any]] = []

        if not has_readme:
            findings.append({
                "rule_id": "DOC_README_MISSING",
                "title": "README Documentation Missing",
                "severity": "high",
                "category": "documentation_quality",
                "explanation": "No README file (.md, .txt) was identified in the project archive. A README is essential for project onboarding.",
                "doc_path": None,
                "location_ref": "Project Root",
                "documented_claim": None,
                "code_evidence": None,
                "verification_status": "potential_inconsistency",
                "faculty_guidance": "Check if documentation was provided in a non-standard location or separate PDF report.",
            })

        if total_words < 50:
            findings.append({
                "rule_id": "DOC_MINIMAL_CONTENT",
                "title": "Insufficient Documentation Content",
                "severity": "high",
                "category": "documentation_quality",
                "explanation": f"Total documentation text contains only {total_words} words across {total_docs} document(s). Insufficient content for evaluation.",
                "doc_path": None,
                "location_ref": "All Documents",
                "documented_claim": None,
                "code_evidence": None,
                "verification_status": "insufficient_evidence",
                "faculty_guidance": "Verify whether documentation files were omitted or submitted in a separate archive.",
            })
        elif total_words < 200:
            findings.append({
                "rule_id": "DOC_LIMITED_CONTENT",
                "title": "Very Limited Documentation Depth",
                "severity": "medium",
                "category": "documentation_quality",
                "explanation": f"Total documentation text contains only {total_words} words. Key architecture and implementation details may be lacking.",
                "doc_path": None,
                "location_ref": "All Documents",
                "documented_claim": None,
                "code_evidence": None,
                "verification_status": "potential_inconsistency",
                "faculty_guidance": "Request student team to submit full project report or detailed design specifications.",
            })

        if not has_setup:
            findings.append({
                "rule_id": "DOC_SETUP_MISSING",
                "title": "Missing Installation / Setup Guide",
                "severity": "high",
                "category": "documentation_quality",
                "explanation": "The documentation does not contain recognizable setup, installation, or execution instructions.",
                "doc_path": None,
                "location_ref": "Setup / Getting Started",
                "documented_claim": None,
                "code_evidence": None,
                "verification_status": "potential_inconsistency",
                "faculty_guidance": "Ask the student team during viva to demonstrate running the application from scratch.",
            })

        if not has_testing:
            findings.append({
                "rule_id": "DOC_TESTING_MISSING",
                "title": "Testing & Results Section Absent",
                "severity": "medium",
                "category": "documentation_quality",
                "explanation": "No testing, verification, or experimental results section was identified in the project documentation.",
                "doc_path": None,
                "location_ref": "Testing Section",
                "documented_claim": None,
                "code_evidence": None,
                "verification_status": "potential_inconsistency",
                "faculty_guidance": "Verify if automated tests exist in the codebase despite absent documentation.",
            })

        if not section_matches["architecture"]["present"]:
            findings.append({
                "rule_id": "DOC_ARCHITECTURE_MISSING",
                "title": "System Architecture / Design Section Absent",
                "severity": "medium",
                "category": "documentation_quality",
                "explanation": "The documentation does not contain an explicit System Architecture, System Design, or Component Diagram section.",
                "doc_path": None,
                "location_ref": "Architecture Section",
                "documented_claim": None,
                "code_evidence": None,
                "verification_status": "potential_inconsistency",
                "faculty_guidance": "Review whether architectural decisions were explained verbally or within code comments.",
            })

        # Calculate preliminary score
        if total_words < 50:
            preliminary_score = None
            score_explanation = {
                "status": "insufficient_evidence",
                "reason": f"Only {total_words} words of extractable documentation detected. A score cannot be reliably computed without adequate text evidence.",
                "factors": [],
                "scoringVersion": "v1.0-deterministic-rubric",
            }
        else:
            factors: List[DocumentationScoreFactor] = []

            # Factor 1: Required Core Sections (Max 35 points, 7 pts each for 5 required sections)
            core_pts = round((required_present / max(required_total, 1)) * 35.0, 1)
            factors.append(
                DocumentationScoreFactor(
                    name="Core Sections Coverage",
                    pointsAwarded=core_pts,
                    maxPoints=35.0,
                    notes=f"{required_present} of {required_total} required sections present (Intro, Setup, Architecture, Implementation, Testing).",
                )
            )

            # Factor 2: Recommended Sections Bonus (Max 15 points, 2.5 pts each for up to 6 optional sections)
            opt_sections = [sec for sec in SECTION_DEFINITIONS if not sec.is_required]
            opt_present = sum(1 for sec in opt_sections if section_matches[sec.key]["present"])
            opt_pts = min(round(opt_present * 2.5, 1), 15.0)
            factors.append(
                DocumentationScoreFactor(
                    name="Recommended & Academic Sections",
                    pointsAwarded=opt_pts,
                    maxPoints=15.0,
                    notes=f"{opt_present} of {len(opt_sections)} optional sections recognized (SRS, Objectives, Methodology, Conclusion, References, Abstract).",
                )
            )

            # Factor 3: Operational Instructions & Setup Quality (Max 20 points)
            setup_pts = 0.0
            setup_notes = []
            if has_setup:
                setup_pts += 10.0
                setup_notes.append("Setup section identified")
                # Check for executable command indicators
                has_cli = any(
                    re.search(r"(?:npm|pip|python|yarn|docker|cargo|mvn|gradle)\s+[a-z]", d.text)
                    for d in documents
                )
                if has_cli:
                    setup_pts += 10.0
                    setup_notes.append("CLI / package management setup commands provided")
                else:
                    setup_pts += 5.0
                    setup_notes.append("Setup text present but few explicit CLI commands")
            else:
                setup_notes.append("No identifiable setup or installation guide found")

            factors.append(
                DocumentationScoreFactor(
                    name="Setup & Operational Instructions",
                    pointsAwarded=setup_pts,
                    maxPoints=20.0,
                    notes="; ".join(setup_notes),
                )
            )

            # Factor 4: Documentation Substance & Depth (Max 20 points)
            if total_words >= 1000:
                depth_pts = 20.0
                depth_notes = f"Comprehensive documentation depth ({total_words} words across {total_docs} files)."
            elif total_words >= 500:
                depth_pts = 15.0
                depth_notes = f"Adequate documentation depth ({total_words} words)."
            elif total_words >= 200:
                depth_pts = 10.0
                depth_notes = f"Moderate documentation depth ({total_words} words)."
            else:
                depth_pts = 5.0
                depth_notes = f"Brief documentation ({total_words} words)."

            factors.append(
                DocumentationScoreFactor(
                    name="Documentation Substance & Depth",
                    pointsAwarded=depth_pts,
                    maxPoints=20.0,
                    notes=depth_notes,
                )
            )

            # Factor 5: Structural Integrity & Clarity (Max 10 points)
            struct_pts = 10.0
            struct_notes = []
            if has_readme:
                struct_notes.append("Standard README file present")
            else:
                struct_pts -= 4.0
                struct_notes.append("README absent (-4 pts)")

            if repetition_warnings:
                struct_pts = max(struct_pts - 3.0, 2.0)
                struct_notes.append(f"{len(repetition_warnings)} repetitive section(s) detected (-3 pts)")
            else:
                struct_notes.append("No repetitive boilerplates detected")

            factors.append(
                DocumentationScoreFactor(
                    name="Structural Integrity & Clarity",
                    pointsAwarded=struct_pts,
                    maxPoints=10.0,
                    notes="; ".join(struct_notes),
                )
            )

            total_score = sum(f.points_awarded for f in factors)
            preliminary_score = round(max(0.0, min(total_score, 100.0)), 1)

            score_explanation = {
                "status": "completed",
                "totalScore": preliminary_score,
                "scoringVersion": "v1.0-deterministic-rubric",
                "factors": [f.model_dump(by_alias=True) for f in factors],
                "summary": (
                    f"Preliminary documentation score of {preliminary_score}/100 calculated from "
                    f"{total_words} extractable words, {recognized_count} recognized sections, "
                    f"and setup instruction evaluation."
                ),
            }

        return (
            metrics,
            coverage_items,
            preliminary_score,
            score_explanation,
            findings,
            all_warnings,
        )
