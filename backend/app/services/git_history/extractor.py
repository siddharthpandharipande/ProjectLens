from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import git
from git.exc import GitError


MAX_INSPECTED_COMMITS = 500
MAX_CHANGED_FILES_PER_COMMIT = 50


class GitCommitExtractor:
    """
    Safely extracts read-only commit metadata and change statistics from a valid Git repository.
    Enforces commit count limits, deduplicates commits across branches, and safely handles merge commits.
    """

    @classmethod
    def extract_commits(
        cls, repo: git.Repo, max_commits: int = MAX_INSPECTED_COMMITS
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Traverses commit history up to max_commits.
        Returns:
            Tuple of (commit_records_list, extraction_warnings_list)
        """
        records: List[Dict[str, Any]] = []
        warnings: List[str] = []
        seen_hashes = set()

        try:
            # Use iter_commits on current active branch / HEAD
            # We iterate safely and stop at max_commits
            commits_iter = repo.iter_commits(max_count=max_commits)
        except GitError as e:
            warnings.append(f"Git log traversal warning: {str(e)}")
            return records, warnings
        except Exception as e:
            warnings.append(f"Unexpected error traversing commits: {str(e)}")
            return records, warnings

        for commit in commits_iter:
            chash = str(commit.hexsha)
            if chash in seen_hashes:
                continue
            seen_hashes.add(chash)

            # 1. Author and timestamp
            author_name = str(commit.author.name) if commit.author and commit.author.name else "Unknown"
            author_email = str(commit.author.email) if commit.author and commit.author.email else ""
            
            try:
                committed_at = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
            except Exception:
                committed_at = datetime.now(timezone.utc)

            subject = str(commit.summary or "")[:500]
            is_merge = len(commit.parents) > 1

            # 2. Line statistics & changed files
            lines_added = 0
            lines_deleted = 0
            files_changed_count = 0
            changed_files_list: List[str] = []

            try:
                # GitPython commit.stats parses change metadata
                # Safe for normal commits and root commits
                stats = commit.stats
                total_stats = stats.total
                lines_added = int(total_stats.get("insertions", 0))
                lines_deleted = int(total_stats.get("deletions", 0))
                files_changed_count = int(total_stats.get("files", 0))
                
                # Extract file paths safely, normalized with forward slashes
                raw_files = list(stats.files.keys())
                for rf in raw_files[:MAX_CHANGED_FILES_PER_COMMIT]:
                    changed_files_list.append(str(rf).replace("\\", "/"))
            except Exception:
                # Fallback for merge commits or binary files without standard diff
                if is_merge:
                    # In Git, merge commits often have no direct diff against multiple parents
                    files_changed_count = 0
                    lines_added = 0
                    lines_deleted = 0
                else:
                    # Inspect diff against first parent if single parent
                    try:
                        if commit.parents:
                            diff_index = commit.diff(commit.parents[0])
                            files_changed_count = len(diff_index)
                            for d in diff_index[:MAX_CHANGED_FILES_PER_COMMIT]:
                                path = d.b_path or d.a_path or ""
                                if path:
                                    changed_files_list.append(str(path).replace("\\", "/"))
                    except Exception:
                        pass

            record = {
                "commit_hash": chash,
                "short_hash": chash[:8],
                "committed_at": committed_at,
                "author_name": author_name,
                "author_email": author_email,
                "subject": subject,
                "files_changed_count": files_changed_count,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "is_merge": is_merge,
                "changed_files": changed_files_list,
            }
            records.append(record)

            if len(records) >= max_commits:
                warnings.append(
                    f"Repository history truncated to maximum configured limit of {max_commits} commits."
                )
                break

        return records, warnings
