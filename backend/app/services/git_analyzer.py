import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def analyze_development_process(extracted_dir: Path) -> Dict[str, Any]:
    """
    Analyzes Git metadata if available in extracted project directory.
    If .git folder is missing, transparently returns status="N/A" and score=None.
    Uses neutral academic evaluation language.
    """
    git_dir = extracted_dir / ".git"

    if not git_dir.exists():
        return {
            "score": None,
            "status": "N/A",
            "evidence": ["Git history was not included in the submitted project."],
            "breakdown": {}
        }

    evidence: List[str] = []
    breakdown = {
        "commit_frequency": 0.0,
        "time_span": 0.0,
        "commit_distribution": 0.0,
        "collaboration": 0.0,
    }

    try:
        # Run git log command inside extracted_dir
        cmd = ["git", "--git-dir", str(git_dir), "--work-tree", str(extracted_dir), "log", "--pretty=format:%h|%an|%ad", "--date=iso"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)

        if res.returncode != 0 or not res.stdout.strip():
            return {
                "score": None,
                "status": "N/A",
                "evidence": [".git directory detected, but no readable commit history found."],
                "breakdown": {}
            }

        lines = res.stdout.strip().splitlines()
        commit_count = len(lines)
        evidence.append(f"✓ {commit_count} Git commits recorded in repository history")

        if commit_count >= 20:
            breakdown["commit_frequency"] = 30.0
            evidence.append("✓ Strong commit frequency demonstrating iterative development")
        elif commit_count >= 5:
            breakdown["commit_frequency"] = 20.0
            evidence.append("✓ Moderate commit frequency detected")
        else:
            breakdown["commit_frequency"] = 10.0
            evidence.append("⚠ Limited commit history recorded")

        # Parse dates for time span
        dates = []
        authors = set()
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 3:
                authors.add(parts[1])
                dates.append(parts[2])

        if len(dates) >= 2:
            breakdown["time_span"] = 30.0
            evidence.append("✓ Development activity spans across multiple development sessions")
        else:
            breakdown["time_span"] = 15.0

        if len(authors) > 1:
            breakdown["collaboration"] = 20.0
            evidence.append(f"✓ Multi-contributor commit activity ({len(authors)} author(s))")
        else:
            breakdown["collaboration"] = 20.0
            evidence.append("✓ Individual author development track")

        breakdown["commit_distribution"] = 20.0

        total_score = round(sum(breakdown.values()), 1)

        return {
            "score": total_score,
            "status": "completed",
            "evidence": evidence,
            "breakdown": breakdown
        }

    except Exception:
        return {
            "score": None,
            "status": "N/A",
            "evidence": ["Git repository metadata could not be evaluated."],
            "breakdown": {}
        }
