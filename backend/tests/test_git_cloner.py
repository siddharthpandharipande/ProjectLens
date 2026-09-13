import pytest
from pathlib import Path
from app.services.git_cloner import validate_git_url, clone_git_repository, GitCloneError

def test_validate_git_url_valid_https():
    is_valid, err = validate_git_url("https://github.com/user/repo.git")
    assert is_valid is True
    assert err is None

def test_validate_git_url_valid_without_dot_git():
    is_valid, err = validate_git_url("https://github.com/user/repo")
    assert is_valid is True
    assert err is None

def test_validate_git_url_invalid_scheme():
    is_valid, err = validate_git_url("ftp://example.com/repo.git")
    assert is_valid is False
    assert "supported" in err.lower()


def test_validate_git_url_forbidden_chars():
    is_valid, err = validate_git_url("https://github.com/user/repo; rm -rf /")
    assert is_valid is False
    assert "Invalid character" in err

def test_validate_git_url_flag_injection():
    is_valid, err = validate_git_url("--upload-pack=calc.exe")
    assert is_valid is False
    assert "cannot start with a hyphen" in err

def test_normalize_git_url():
    from app.services.git_cloner import normalize_git_url
    assert normalize_git_url("https://github.com/user/repo/tree/main?tab=readme") == "https://github.com/user/repo"
    assert normalize_git_url("https://github.com/user/repo.git/") == "https://github.com/user/repo.git"

def test_clone_git_repository_invalid_url_raises_error(tmp_path: Path):
    target = tmp_path / "cloned_repo"
    with pytest.raises(GitCloneError) as exc_info:
        clone_git_repository("invalid-url", target)
    assert "supported" in str(exc_info.value).lower()


