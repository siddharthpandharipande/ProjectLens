import os
import re
import shutil
import zipfile
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

class GitCloneError(Exception):
    """Exception raised when cloning a Git repository fails."""
    pass

def normalize_git_url(url: str) -> str:
    """
    Normalizes user-submitted repository URL:
    - Removes query parameters
    - Strips /tree/branch, /blob/branch, or subpath components
    - Normalizes GitHub/GitLab web URLs to standard clone endpoint
    """
    cleaned = url.strip()
    cleaned = re.sub(r'\?.*$', '', cleaned)
    cleaned = re.sub(r'/(tree|blob)/.*$', '', cleaned)
    cleaned = cleaned.rstrip("/.")
    return cleaned

def validate_git_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate and normalize user-submitted Git repository URL.
    Returns (is_valid: bool, error_message: Optional[str]).
    Enforces security checks to prevent shell injection, unsafe schemes, or invalid format.
    """
    if not url or not isinstance(url, str):
        return False, "Repository URL is required."

    cleaned_url = normalize_git_url(url)

    # Reject dangerous characters that could lead to command injection or flag injection
    forbidden_chars = [";", "&", "|", "`", "$", "\n", "\r", "\t", '"', "'", "<", ">", "(", ")"]
    for char in forbidden_chars:
        if char in cleaned_url:
            return False, f"Invalid character in repository URL: '{char}'"

    # Reject flag injection (URL starting with -)
    if cleaned_url.startswith("-"):
        return False, "Repository URL cannot start with a hyphen."

    # Reject non-HTTP/HTTPS/file schemes
    if not (cleaned_url.startswith("http://") or cleaned_url.startswith("https://") or cleaned_url.startswith("file://")):
        return False, "Only public HTTP, HTTPS, or file:// repository URLs are supported (e.g., https://github.com/user/repo)."

    # Basic pattern match for host/path
    url_pattern = re.compile(r'^(?:https?|file)://[a-zA-Z0-9\.\-_/:\\]+$')
    if not url_pattern.match(cleaned_url):
        return False, "Invalid Git repository URL format. Please provide a valid URL like https://github.com/user/repository."

    return True, None

def try_github_archive_fallback(repo_url: str, target_dir: Path) -> bool:
    """
    Fallback method: If git CLI clone fails (e.g. CLI issues or network restrictions),
    attempts to download GitHub repository ZIP archive directly via HTTP.
    """
    if "github.com" not in repo_url.lower():
        return False

    clean = repo_url.rstrip("/.").replace(".git", "")
    branches = ["main", "master"]

    for branch in branches:
        zip_url = f"{clean}/archive/refs/heads/{branch}.zip"
        zip_path = target_dir.parent / f"fallback_{target_dir.name}.zip"
        try:
            req = urllib.request.Request(
                zip_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjectLens/2.4"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(zip_path, "wb") as f:
                f.write(resp.read())

            if zip_path.exists() and zip_path.stat().st_size > 0:
                if target_dir.exists():
                    shutil.rmtree(target_dir, ignore_errors=True)
                target_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(target_dir)

                # If extracted into a single wrapper directory, move files up
                subdirs = [d for d in target_dir.iterdir() if d.is_dir()]
                if len(subdirs) == 1 and not any(f.is_file() for f in target_dir.iterdir()):
                    wrapper = subdirs[0]
                    for item in wrapper.iterdir():
                        shutil.move(str(item), str(target_dir / item.name))
                    shutil.rmtree(wrapper, ignore_errors=True)

                if zip_path.exists():
                    zip_path.unlink()

                return True
        except Exception:
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except Exception:
                    pass
    return False

def clone_git_repository(repo_url: str, target_dir: Path, timeout_seconds: int = 90) -> Path:
    """
    Clones a remote Git repository into an isolated target directory.
    Uses --no-single-branch without shallow depth to preserve complete commit history.
    Includes HTTP ZIP archive fallback for GitHub repositories if git clone encounters errors.
    """
    is_valid, err_msg = validate_git_url(repo_url)
    if not is_valid:
        raise GitCloneError(err_msg or "Invalid Git repository URL.")

    cleaned_url = normalize_git_url(repo_url)

    # Clean target directory if exists
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "git",
        "clone",
        "--no-single-branch",
        cleaned_url,
        str(target_dir)
    ]

    clone_env = dict(os.environ)
    clone_env["GIT_TERMINAL_PROMPT"] = "0"

    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            env=clone_env
        )

        if res.returncode != 0:
            stderr_msg = res.stderr.strip() if res.stderr else "Clone failed"

            # Check for private repository or missing auth indicators
            auth_keywords = ["could not read username", "authentication failed", "repository not found", "access denied", "403", "401"]
            if any(kw in stderr_msg.lower() for kw in auth_keywords):
                raise GitCloneError("Private repository authentication is not configured. Please ensure the repository is public or upload a project ZIP.")

            # Attempt HTTP archive fallback
            if try_github_archive_fallback(cleaned_url, target_dir):
                return target_dir

            raise GitCloneError(f"Repository acquisition failed: {stderr_msg}")

        return target_dir

    except subprocess.TimeoutExpired:
        if try_github_archive_fallback(cleaned_url, target_dir):
            return target_dir
        shutil.rmtree(target_dir, ignore_errors=True)
        raise GitCloneError(f"Repository acquisition timed out after {timeout_seconds} seconds. Please check repository size or network connectivity.")
    except Exception as e:
        if not isinstance(e, GitCloneError):
            if try_github_archive_fallback(cleaned_url, target_dir):
                return target_dir
            raise GitCloneError(f"Repository clone error: {str(e)}")
        raise e


