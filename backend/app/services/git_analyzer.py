import os
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def parse_iso_date(date_str: str) -> Optional[datetime]:
    """Parse ISO date string from Git log."""
    try:
        # e.g., "2026-01-15 14:30:00 +0000" -> "2026-01-15"
        clean_date = date_str.strip().split()[0]
        return datetime.strptime(clean_date, "%Y-%m-%d")
    except Exception:
        return None

def analyze_development_process(extracted_dir: Path) -> Dict[str, Any]:
    """
    Analyzes Git metadata if available in extracted project directory.
    Extracts real commit history: count, timeline, lines added/deleted, authors, and commit distribution.
    If .git folder is missing or dummy dir is passed, transparently returns status="N/A" and score=None.
    """
    empty_result = {
        "score": None,
        "status": "N/A",
        "evidence": ["Git history was not included in the submitted project."],
        "breakdown": {},
        "git_history": {"available": False}
    }

    if not extracted_dir or str(extracted_dir) in {".", "./", ""}:
        return empty_result

    git_dir = extracted_dir / ".git"
    if not git_dir.exists():
        return empty_result

    evidence: List[str] = []
    breakdown = {
        "commit_frequency": 0.0,
        "time_span": 0.0,
        "commit_distribution": 0.0,
        "collaboration": 0.0,
    }

    try:
        # 1. Fetch commit log with commit hash, author, date, and subject
        cmd_log = [
            "git", "log", "-n", "500", "--pretty=format:%H|%an|%ad|%s", "--date=short"
        ]
        res_log = subprocess.run(cmd_log, cwd=str(extracted_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)

        if res_log.returncode != 0 or not res_log.stdout.strip():
            return {
                "score": None,
                "status": "N/A",
                "evidence": [".git directory detected, but no readable commit history found."],
                "breakdown": {},
                "git_history": {"available": False}
            }

        commit_lines = res_log.stdout.strip().splitlines()
        commit_count = len(commit_lines)

        dates: List[datetime] = []
        date_strings: List[str] = []
        authors: set = set()
        
        for line in commit_lines:
            parts = line.split("|")
            if len(parts) >= 3:
                author_name = parts[1].strip()
                if author_name:
                    authors.add(author_name)
                dt_str = parts[2].strip()
                dt = parse_iso_date(dt_str)
                if dt:
                    dates.append(dt)
                    date_strings.append(dt_str)

        # First and last commit dates
        dates.sort()
        first_commit_str = dates[0].strftime("%Y-%m-%d") if dates else "Unknown"
        last_commit_str = dates[-1].strftime("%Y-%m-%d") if dates else "Unknown"
        dev_days = (dates[-1] - dates[0]).days + 1 if len(dates) >= 2 else 1

        # 2. Fetch numstat for lines added / deleted and files changed
        cmd_stat = [
            "git", "log", "-n", "500", "--numstat", "--pretty=format:COMMIT:%H"
        ]
        res_stat = subprocess.run(cmd_stat, cwd=str(extracted_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)



        lines_added = 0
        lines_deleted = 0
        modified_files: set = set()
        commit_changes: Dict[str, int] = {}
        current_commit_hash = None

        if res_stat.returncode == 0 and res_stat.stdout:
            for s_line in res_stat.stdout.splitlines():
                s_line = s_line.strip()
                if s_line.startswith("COMMIT:"):
                    current_commit_hash = s_line.split("COMMIT:")[1]
                    commit_changes[current_commit_hash] = 0
                elif s_line:
                    parts = re.split(r'\s+', s_line)
                    if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                        ins = int(parts[0])
                        dels = int(parts[1])
                        filepath = parts[2]
                        lines_added += ins
                        lines_deleted += dels
                        modified_files.add(filepath)
                        if current_commit_hash:
                            commit_changes[current_commit_hash] += (ins + dels)

        largest_commit_lines = max(commit_changes.values()) if commit_changes else 0

        # --- SCORING & EVIDENCE ---
        evidence.append(f"✓ {commit_count} Git commits recorded across {dev_days}-day development period")
        evidence.append(f"✓ {lines_added:,} lines added, {lines_deleted:,} lines deleted across {len(modified_files)} files")
        evidence.append(f"✓ Development timeline: {first_commit_str} → {last_commit_str}")

        # Commit frequency score (30%)
        if commit_count >= 20:
            breakdown["commit_frequency"] = 30.0
            evidence.append("✓ High commit frequency demonstrating iterative development")
        elif commit_count >= 5:
            breakdown["commit_frequency"] = 22.0
            evidence.append("✓ Moderate commit frequency detected")
        else:
            breakdown["commit_frequency"] = 12.0
            evidence.append("⚠ Limited commit frequency recorded")

        # Time span score (30%)
        if dev_days >= 14:
            breakdown["time_span"] = 30.0
            evidence.append(f"✓ Extended development span ({dev_days} days)")
        elif dev_days >= 3:
            breakdown["time_span"] = 22.0
            evidence.append(f"✓ Multi-day development activity ({dev_days} days)")
        else:
            breakdown["time_span"] = 15.0
            evidence.append("⚠ Single/short session development timeline")

        # Collaboration (20%)
        author_count = len(authors)
        if author_count > 1:
            breakdown["collaboration"] = 20.0
            evidence.append(f"✓ Multi-contributor activity ({author_count} authors: {', '.join(list(authors)[:3])})")
        else:
            breakdown["collaboration"] = 20.0
            evidence.append(f"✓ Single author development track ({list(authors)[0] if authors else 'Author'})")

        # Commit distribution (20%)
        if largest_commit_lines > 500 and lines_added > 0 and (largest_commit_lines / (lines_added + lines_deleted + 1)) > 0.6:
            breakdown["commit_distribution"] = 10.0
            evidence.append(f"⚠ Large commit detected ({largest_commit_lines:,} lines changed in a single commit)")
        else:
            breakdown["commit_distribution"] = 20.0
            evidence.append("✓ Balanced commit distribution across repository history")

        total_score = round(sum(breakdown.values()), 1)

        git_history_data = {
            "available": True,
            "commit_count": commit_count,
            "first_commit": first_commit_str,
            "last_commit": last_commit_str,
            "development_days": dev_days,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "files_changed": len(modified_files),
            "author_count": author_count,
            "authors": list(authors),
            "largest_commit_lines": largest_commit_lines,
        }

        return {
            "score": total_score,
            "status": "completed",
            "evidence": evidence,
            "breakdown": breakdown,
            "git_history": git_history_data
        }

    except Exception as e:
        return {
            "score": None,
            "status": "N/A",
            "evidence": [f"Git repository history could not be evaluated: {str(e)}"],
            "breakdown": {},
            "git_history": {"available": False}
        }
