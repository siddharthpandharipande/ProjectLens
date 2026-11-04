"""
Development-pattern signal generator for Git history analysis.

Produces advisory findings based on observable commit patterns.
No definitive verdict is ever returned — all signals are advisory and require faculty review.

Signal categories:
  - commit_concentration: Large proportion of changes in few commits
  - timestamp_anomaly: Many commits with identical or unusual timestamps
  - history_duration: Very short recorded history
  - dormancy_gap: Large gaps between recorded commits
  - contributor_distribution: Unusual contributor patterns (informational, not conclusive)
"""
from typing import List, Dict, Any

# Configurable thresholds
LARGE_SINGLE_COMMIT_THRESHOLD = 70.0   # % of total churn in single commit → signal
TOP_3_CONCENTRATION_THRESHOLD = 90.0   # % of total churn in top-3 commits → signal
IDENTICAL_TIMESTAMP_THRESHOLD = 3      # ≥N commits with same timestamp → signal
SHORT_HISTORY_THRESHOLD_DAYS = 3.0     # ≤N days of recorded history → signal
DORMANCY_GAP_DAYS_THRESHOLD = 14.0     # ≥N days gap between any two consecutive commits
SINGLE_COMMIT_ADVISORY = True          # Always produce advisory if only 1 commit


FACULTY_ADVISORY_BOILERPLATE = (
    "This is an advisory observation only. Git metadata can be altered or may be incomplete. "
    "No automated system can determine actual authorship or development timeline from commit records alone. "
    "Faculty review of the full submission is required before drawing any conclusions."
)


def generate_development_signals(
    aggregated: Dict[str, Any],
    commit_records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Produces a list of advisory development-pattern findings.
    Returns list of finding dicts with keys:
        signal_id, title, severity, category, explanation, evidence, faculty_guidance
    """
    findings: List[Dict[str, Any]] = []
    total_commits = aggregated.get("total_commits", 0)

    if total_commits == 0:
        return findings

    # --- 1. Single-commit repository advisory ---
    if total_commits == 1 and SINGLE_COMMIT_ADVISORY:
        findings.append({
            "signal_id": "GIT_SINGLE_COMMIT",
            "title": "Repository Contains Only One Recorded Commit",
            "severity": "advisory",
            "category": "history_duration",
            "explanation": (
                "The repository contains exactly one commit. The recorded history does not reflect "
                "incremental development. This may indicate the project was developed externally and "
                "committed as a single archive, or that intermediate history was removed before submission."
            ),
            "evidence": {"total_commits": total_commits},
            "faculty_guidance": FACULTY_ADVISORY_BOILERPLATE,
        })

    # --- 2. Large proportion of changes in a single commit ---
    largest_share = aggregated.get("largest_commit_share_percent")
    total_additions = aggregated.get("total_additions", 0)
    total_deletions = aggregated.get("total_deletions", 0)
    total_churn = total_additions + total_deletions

    if largest_share is not None and largest_share >= LARGE_SINGLE_COMMIT_THRESHOLD and total_churn > 0:
        findings.append({
            "signal_id": "GIT_LARGE_SINGLE_COMMIT_CONCENTRATION",
            "title": f"Single Commit Accounts for {largest_share:.1f}% of Total Line Changes",
            "severity": "medium",
            "category": "commit_concentration",
            "explanation": (
                f"One commit contains {largest_share:.1f}% of all recorded line changes "
                f"({total_churn:,} total lines across {total_commits} commit(s)). "
                "A large concentration of changes in a single commit is an observable pattern "
                "that faculty may wish to examine alongside the submission."
            ),
            "evidence": {
                "largest_commit_share_percent": largest_share,
                "total_line_churn": total_churn,
                "total_commits": total_commits,
            },
            "faculty_guidance": FACULTY_ADVISORY_BOILERPLATE,
        })

    # --- 3. Top-3 commit concentration ---
    top3_share = aggregated.get("top_3_commit_share_percent")
    if (
        top3_share is not None
        and top3_share >= TOP_3_CONCENTRATION_THRESHOLD
        and total_commits > 3
        and total_churn > 0
    ):
        findings.append({
            "signal_id": "GIT_TOP3_COMMIT_CONCENTRATION",
            "title": f"Top 3 Commits Account for {top3_share:.1f}% of Total Line Changes",
            "severity": "low",
            "category": "commit_concentration",
            "explanation": (
                f"The three largest commits (by lines changed) account for {top3_share:.1f}% "
                f"of all recorded line changes. This indicates commit activity was heavily "
                "concentrated rather than incrementally distributed across the development timeline."
            ),
            "evidence": {
                "top_3_commit_share_percent": top3_share,
                "total_commits": total_commits,
                "total_line_churn": total_churn,
            },
            "faculty_guidance": FACULTY_ADVISORY_BOILERPLATE,
        })

    # --- 4. Short history duration ---
    duration_days = aggregated.get("duration_days", 0.0)
    if duration_days <= SHORT_HISTORY_THRESHOLD_DAYS and total_commits > 1:
        findings.append({
            "signal_id": "GIT_SHORT_HISTORY_DURATION",
            "title": f"Recorded Development Spans Only {duration_days:.1f} Day(s)",
            "severity": "advisory",
            "category": "history_duration",
            "explanation": (
                f"The earliest and latest recorded commits are {duration_days:.1f} days apart. "
                "A very short recorded development window may indicate that intermediate development "
                "history was not included in the submission or that commits were squashed before packaging."
            ),
            "evidence": {
                "duration_days": duration_days,
                "first_commit_at": str(aggregated.get("first_commit_at", "")),
                "last_commit_at": str(aggregated.get("last_commit_at", "")),
                "total_commits": total_commits,
            },
            "faculty_guidance": FACULTY_ADVISORY_BOILERPLATE,
        })

    # --- 5. Identical commit timestamps ---
    if commit_records:
        timestamp_counts: Dict[str, int] = {}
        for c in commit_records:
            ts_str = c["committed_at"].strftime("%Y-%m-%dT%H:%M:%S") if c.get("committed_at") else ""
            if ts_str:
                timestamp_counts[ts_str] = timestamp_counts.get(ts_str, 0) + 1
        max_identical = max(timestamp_counts.values()) if timestamp_counts else 0
        if max_identical >= IDENTICAL_TIMESTAMP_THRESHOLD:
            findings.append({
                "signal_id": "GIT_IDENTICAL_TIMESTAMPS",
                "title": f"{max_identical} Commits Share an Identical Timestamp",
                "severity": "medium",
                "category": "timestamp_anomaly",
                "explanation": (
                    f"{max_identical} commits were recorded at exactly the same timestamp (to the second). "
                    "Identical commit timestamps are unusual in normal incremental development. "
                    "They may result from rebasing, squashing, history rewriting, or scripted commit generation."
                ),
                "evidence": {
                    "max_commits_with_same_timestamp": max_identical,
                    "total_commits": total_commits,
                },
                "faculty_guidance": FACULTY_ADVISORY_BOILERPLATE,
            })

    # --- 6. Dormancy gap ---
    if len(commit_records) >= 2:
        chronological = sorted(commit_records, key=lambda c: c["committed_at"])
        max_gap_days = 0.0
        for i in range(1, len(chronological)):
            gap = (chronological[i]["committed_at"] - chronological[i - 1]["committed_at"]).total_seconds() / 86400.0
            if gap > max_gap_days:
                max_gap_days = gap
        if max_gap_days >= DORMANCY_GAP_DAYS_THRESHOLD:
            findings.append({
                "signal_id": "GIT_DORMANCY_GAP",
                "title": f"Longest Gap Between Consecutive Commits: {max_gap_days:.1f} Days",
                "severity": "low",
                "category": "dormancy_gap",
                "explanation": (
                    f"The longest recorded gap between consecutive commits is {max_gap_days:.1f} days. "
                    "Significant gaps in recorded commit activity may indicate periods of inactivity "
                    "or that work was performed outside of the Git repository during that period."
                ),
                "evidence": {
                    "max_gap_days": round(max_gap_days, 2),
                    "total_commits": total_commits,
                },
                "faculty_guidance": FACULTY_ADVISORY_BOILERPLATE,
            })

    return findings
