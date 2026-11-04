from datetime import datetime
import statistics
from typing import List, Dict, Any, Optional


class GitTimelineAggregator:
    """
    Aggregates commit records into a chronological timeline and computes project-level
    cadence, contributor, and volume statistics.
    """

    WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    @classmethod
    def aggregate_timeline(
        cls, commit_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Processes commit records and returns aggregated summary data.
        Assumes commit_records contains raw extracted dicts.
        """
        if not commit_records:
            return {
                "total_commits": 0,
                "distinct_contributors_count": 0,
                "first_commit_at": None,
                "last_commit_at": None,
                "duration_days": 0.0,
                "total_files_changed": 0,
                "total_additions": 0,
                "total_deletions": 0,
                "avg_time_between_commits_hours": None,
                "median_time_between_commits_hours": None,
                "largest_commit_share_percent": None,
                "top_3_commit_share_percent": None,
                "activity_by_day": {},
                "activity_by_weekday": {},
                "size_distribution": {
                    "small (<50 lines)": 0,
                    "medium (50-250 lines)": 0,
                    "large (>250 lines)": 0,
                },
                "contributors": [],
            }

        # Sort commits chronologically (oldest first for delta & duration calculations)
        chronological_commits = sorted(
            commit_records, key=lambda c: c["committed_at"]
        )

        total_commits = len(chronological_commits)
        first_commit_at = chronological_commits[0]["committed_at"]
        last_commit_at = chronological_commits[-1]["committed_at"]

        # Duration in days
        delta = last_commit_at - first_commit_at
        duration_days = max(round(delta.total_seconds() / 86400.0, 2), 0.0)

        # 1. Intervals between consecutive commits
        intervals_hours: List[float] = []
        for i in range(1, len(chronological_commits)):
            diff = (
                chronological_commits[i]["committed_at"]
                - chronological_commits[i - 1]["committed_at"]
            ).total_seconds() / 3600.0
            if diff >= 0:
                intervals_hours.append(round(diff, 2))

        avg_hours = None
        median_hours = None
        if intervals_hours:
            avg_hours = round(statistics.mean(intervals_hours), 2)
            median_hours = round(statistics.median(intervals_hours), 2)

        # 2. Activity by day and weekday
        activity_by_day: Dict[str, int] = {}
        activity_by_weekday: Dict[str, int] = {day: 0 for day in cls.WEEKDAY_NAMES}

        # 3. Size distribution and totals
        total_files_changed = 0
        total_additions = 0
        total_deletions = 0
        commit_churn_list: List[int] = []

        size_distribution = {
            "small (<50 lines)": 0,
            "medium (50-250 lines)": 0,
            "large (>250 lines)": 0,
        }

        # 4. Contributors tracking
        contributors_map: Dict[str, Dict[str, Any]] = {}

        for c in chronological_commits:
            dt: datetime = c["committed_at"]
            day_str = dt.strftime("%Y-%m-%d")
            weekday_str = cls.WEEKDAY_NAMES[dt.weekday()]

            activity_by_day[day_str] = activity_by_day.get(day_str, 0) + 1
            activity_by_weekday[weekday_str] = activity_by_weekday.get(weekday_str, 0) + 1

            files_count = c.get("files_changed_count", 0)
            added = c.get("lines_added", 0)
            deleted = c.get("lines_deleted", 0)
            churn = added + deleted

            total_files_changed += files_count
            total_additions += added
            total_deletions += deleted
            commit_churn_list.append(churn)

            # Categorize size
            if churn < 50:
                size_distribution["small (<50 lines)"] += 1
            elif churn <= 250:
                size_distribution["medium (50-250 lines)"] += 1
            else:
                size_distribution["large (>250 lines)"] += 1

            # Contributor key normalized
            author = (c.get("author_name") or "Unknown").strip()
            email = (c.get("author_email") or "").strip().lower()
            key = f"{author} <{email}>" if email else author

            if key not in contributors_map:
                contributors_map[key] = {
                    "name": author,
                    "email": email,
                    "commit_count": 0,
                    "additions": 0,
                    "deletions": 0,
                }
            contributors_map[key]["commit_count"] += 1
            contributors_map[key]["additions"] += added
            contributors_map[key]["deletions"] += deleted

        # Compute percentage for contributors
        contributors_list: List[Dict[str, Any]] = []
        for item in sorted(
            contributors_map.values(), key=lambda x: x["commit_count"], reverse=True
        ):
            pct = round((item["commit_count"] / total_commits) * 100.0, 1)
            item["percentage"] = pct
            contributors_list.append(item)

        # 5. Largest commit share %
        total_churn = total_additions + total_deletions
        largest_commit_share = None
        top_3_commit_share = None

        if total_churn > 0 and commit_churn_list:
            sorted_churn = sorted(commit_churn_list, reverse=True)
            largest_commit_share = round((sorted_churn[0] / total_churn) * 100.0, 1)
            top_3_sum = sum(sorted_churn[:3])
            top_3_commit_share = round((top_3_sum / total_churn) * 100.0, 1)

        return {
            "total_commits": total_commits,
            "distinct_contributors_count": len(contributors_list),
            "first_commit_at": first_commit_at,
            "last_commit_at": last_commit_at,
            "duration_days": duration_days,
            "total_files_changed": total_files_changed,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "avg_time_between_commits_hours": avg_hours,
            "median_time_between_commits_hours": median_hours,
            "largest_commit_share_percent": largest_commit_share,
            "top_3_commit_share_percent": top_3_commit_share,
            "activity_by_day": activity_by_day,
            "activity_by_weekday": activity_by_weekday,
            "size_distribution": size_distribution,
            "contributors": contributors_list,
        }
