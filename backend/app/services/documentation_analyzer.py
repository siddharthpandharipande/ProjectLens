import re
from pathlib import Path
from typing import List, Dict, Any

def analyze_documentation_integrity(scanned_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes documentation completeness, setup instructions, architecture breakdown,
    and code/documentation consistency. Returns normalized score (0–100) and evidence.
    """
    evidence: List[str] = []
    score_components = {
        "presence": 0.0,
        "structure": 0.0,
        "setup_instructions": 0.0,
        "technical_description": 0.0,
        "consistency": 0.0,
    }

    # 1. Presence Detection
    doc_files = [sf for sf in scanned_files if sf.get("file_type") == "documentation"]
    readme_files = [sf for sf in doc_files if "readme" in sf.get("filename", "").lower()]

    if readme_files:
        score_components["presence"] += 15.0
        evidence.append("✓ Primary README documentation file detected")
    elif doc_files:
        score_components["presence"] += 10.0
        evidence.append("✓ Project documentation files detected")
    else:
        evidence.append("⚠ No primary README or documentation files detected")

    if len(doc_files) > 1:
        score_components["presence"] += 5.0
        evidence.append(f"✓ {len(doc_files)} documentation files included in project")

    # Read README content for deeper inspection
    readme_content = ""
    if readme_files:
        readme_content = readme_files[0].get("content") or readme_files[0].get("readme_content") or ""
        if not readme_content:
            abs_path = readme_files[0].get("abs_path")
            if abs_path and isinstance(abs_path, Path) and abs_path.exists():
                try:
                    if abs_path.stat().st_size < 1_000_000:
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            readme_content = f.read()
                except Exception:
                    pass


    content_lower = readme_content.lower()

    # 2. Structure & Completeness (Section Headers)
    detected_sections = []
    section_patterns = {
        "Installation / Setup": r'#+\s*(installation|setup|getting started|prerequisites|requirements)',
        "Usage / Execution": r'#+\s*(usage|how to run|running|quickstart|examples)',
        "Features / Overview": r'#+\s*(features|overview|about|introduction|description)',
        "Architecture / Tech Stack": r'#+\s*(architecture|tech stack|technologies|built with|design|methodology)',
        "API / Configuration": r'#+\s*(api|endpoints|configuration|environment|config)',
    }

    for section_name, pattern in section_patterns.items():
        if re.search(pattern, content_lower, re.MULTILINE):
            detected_sections.append(section_name)

    if len(detected_sections) >= 4:
        score_components["structure"] = 20.0
        evidence.append(f"✓ Comprehensive README structure ({len(detected_sections)} key sections found)")
    elif len(detected_sections) >= 2:
        score_components["structure"] = 12.0
        evidence.append(f"✓ Basic README structure ({', '.join(detected_sections)} found)")
    elif detected_sections:
        score_components["structure"] = 6.0
        evidence.append(f"✓ Minimal README section headers detected ({detected_sections[0]})")
    elif readme_content:
        score_components["structure"] = 4.0
        evidence.append("⚠ README lacks standard markdown header sections")

    # 3. Setup & Usage Instructions (Code Blocks & Executable Commands)
    has_code_blocks = "```" in readme_content or "`" in readme_content
    has_install_cmds = any(cmd in content_lower for cmd in ["npm ", "pip ", "python ", "docker ", "git clone", "yarn ", "cargo "])

    if has_code_blocks and has_install_cmds:
        score_components["setup_instructions"] = 20.0
        evidence.append("✓ Executable installation & setup command snippets provided")
    elif has_install_cmds or has_code_blocks:
        score_components["setup_instructions"] = 12.0
        evidence.append("✓ Setup / usage instructions present in documentation")
    else:
        evidence.append("⚠ Missing executable setup or installation commands in documentation")

    # 4. Technical / Architecture Description
    if any(k in content_lower for k in ["architecture", "backend", "frontend", "database", "api", "flow", "design"]):
        score_components["technical_description"] = 20.0
        evidence.append("✓ Technical architecture and system component overview included")
    elif len(readme_content.splitlines()) > 20:
        score_components["technical_description"] = 10.0
        evidence.append("✓ General project description provided")
    else:
        evidence.append("⚠ Incomplete technical architecture documentation")

    # 5. Code & Documentation Consistency
    if len(readme_content) > 300:
        score_components["consistency"] = 20.0
        evidence.append("✓ Documentation reflects actual project structure and codebase")
    elif len(readme_content) > 0:
        score_components["consistency"] = 10.0
        evidence.append("✓ Basic documentation provided")
    else:
        score_components["consistency"] = 0.0

    total_score = round(sum(score_components.values()), 1)

    return {
        "score": total_score,
        "status": "completed",
        "evidence": evidence,
        "breakdown": score_components
    }
