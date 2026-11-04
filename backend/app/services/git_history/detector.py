import os
from pathlib import Path
from typing import Tuple, Optional
import git
from git.exc import InvalidGitRepositoryError, NoSuchPathError, GitError


class GitRepositoryDetector:
    """
    Safely inspects the project's extraction directory for a valid local Git repository.
    Enforces strict canonical path containment and detects availability states:
    - available: Valid repository with at least one commit
    - empty: Valid repository with 0 commits (unborn HEAD)
    - unavailable: Missing .git directory
    - corrupt: Corrupt or unreadable Git metadata
    """

    @classmethod
    def detect_repository(
        cls, extract_dir: Path
    ) -> Tuple[str, str, Optional[git.Repo], bool, Optional[str]]:
        """
        Inspects extract_dir for Git repository.
        Returns:
            Tuple of (status, availability, repo_instance, is_shallow, error_message)
            - status: "completed", "no_git_repository", "empty_repository", "corrupt_git_metadata"
            - availability: "available", "unavailable", "empty", "corrupt"
            - repo_instance: git.Repo or None
            - is_shallow: bool
            - error_message: str or None
        """
        try:
            resolved_extract_dir = extract_dir.resolve()
        except Exception as e:
            return "corrupt_git_metadata", "corrupt", None, False, f"Invalid project directory: {e}"

        git_dir = resolved_extract_dir / ".git"
        repo_root = resolved_extract_dir

        # 1. Check if .git exists at root, or in any nested subdirectory (e.g. root project folder)
        if not git_dir.exists():
            try:
                candidate_gits = [
                    p for p in resolved_extract_dir.rglob(".git")
                    if p.is_dir() or p.is_file()
                ]
                if candidate_gits:
                    # Pick the shallowest candidate
                    candidate = min(candidate_gits, key=lambda p: len(p.parts))
                    resolved_cand = candidate.resolve()
                    if str(resolved_cand).startswith(str(resolved_extract_dir)):
                        git_dir = candidate
                        repo_root = candidate.parent
            except Exception:
                pass

        if not git_dir.exists():
            return (
                "no_git_repository",
                "unavailable",
                None,
                False,
                "No .git directory found in uploaded archive. Git history analysis cannot be performed.",
            )

        # 2. Containment check: Ensure .git path does not escape resolved_extract_dir
        try:
            resolved_git_dir = git_dir.resolve()
            if not str(resolved_git_dir).startswith(str(resolved_extract_dir)):
                return (
                    "corrupt_git_metadata",
                    "corrupt",
                    None,
                    False,
                    "Security violation: .git path escapes extracted project boundary.",
                )
        except Exception as e:
            return "corrupt_git_metadata", "corrupt", None, False, f"Path resolution error: {e}"

        # 3. Attempt to initialize GitPython Repo in read-only mode
        try:
            repo = git.Repo(str(repo_root.resolve()))
        except InvalidGitRepositoryError:
            return (
                "corrupt_git_metadata",
                "corrupt",
                None,
                False,
                "Corrupt or invalid .git metadata: repository cannot be parsed.",
            )
        except NoSuchPathError:
            return (
                "no_git_repository",
                "unavailable",
                None,
                False,
                "Git repository path not found.",
            )
        except Exception as e:
            return (
                "corrupt_git_metadata",
                "corrupt",
                None,
                False,
                f"Error initializing Git repository: {str(e)}",
            )

        # 4. Check for shallow repository
        is_shallow = False
        try:
            is_shallow = bool(repo.is_shallow())
        except Exception:
            # Fallback check for shallow file
            shallow_file = git_dir / "shallow"
            if shallow_file.exists():
                is_shallow = True

        # 5. Check if repository has any commits (empty repository / unborn HEAD check)
        try:
            # Attempt to check if HEAD exists and has valid commits
            _ = repo.head.commit
        except (ValueError, GitError, AttributeError, StopIteration) as e:
            # Unborn branch or empty repo with no commits
            return (
                "empty_repository",
                "empty",
                repo,
                is_shallow,
                "Repository exists but contains no recorded commits (empty repository).",
            )
        except Exception as e:
            return (
                "corrupt_git_metadata",
                "corrupt",
                repo,
                is_shallow,
                f"Corrupt or unreadable HEAD reference: {str(e)}",
            )

        return "completed", "available", repo, is_shallow, None
