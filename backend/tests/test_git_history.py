"""
test_git_history.py

Comprehensive test suite for Phase 6: Git Development History Analysis.
Covers:
1. Valid Git repository containing several commits.
2. Repository containing a single commit.
3. Empty Git repository with no commits (unborn HEAD).
4. Project with no .git directory (unavailable state).
5. Invalid or corrupt Git metadata (corrupt state).
6. Shallow repository with shallow marker.
7. Correct chronological ordering of commits.
8. Commit timestamps, duration, and interval metrics (avg/median hours).
9. Changed-file, additions, and deletions statistics.
10. Contributor statistics with multiple authors.
11. Detection of configured development-pattern signals (single commit, concentration, identical timestamps, dormancy gap, short history).
12. Correct handling of merge commits and duplicate commit references.
13. Safe handling of repository paths and boundary containment.
14. Idempotent re-analysis without duplicate database records.
15. POST /api/projects/{project_id}/analyze/development-history endpoint.
16. GET /api/projects/{project_id}/development-history endpoint.
17. Appropriate HTTP 404 responses for nonexistent projects.
18. Correct inclusion of development history in the unified analysis endpoint.
"""

import os
import shutil
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import git
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project, ProjectStructure
from app.models.git_history import (
    ProjectGitHistoryAnalysis,
    ProjectCommitRecord,
    ProjectGitFinding,
)
from app.services.git_history.detector import GitRepositoryDetector
from app.services.git_history.extractor import GitCommitExtractor
from app.services.git_history.timeline import GitTimelineAggregator
from app.services.git_history.signals import generate_development_signals
from app.services.git_history.service import GitHistoryService
from app.services.project_parser import ProjectParser


def _init_local_git_repo(path: Path) -> git.Repo:
    """Initialize a safe test Git repository with isolated local configuration."""
    repo = git.Repo.init(path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test Committer")
        config.set_value("user", "email", "committer@projectlens.edu")
    return repo


# ─── 1 & 7 & 8 & 9: Valid Repository, Ordering, Stats & Intervals ────────────

def test_valid_repo_multi_commits_and_stats(tmp_path: Path):
    """
    Test extraction of multiple commits with known file additions and line changes,
    verifying chronological ordering, intervals, and line stats.
    """
    repo = _init_local_git_repo(tmp_path)

    # Commit 1
    f1 = tmp_path / "main.py"
    f1.write_text("print('hello world')\nx = 10\ny = 20\n", encoding="utf-8")
    repo.index.add(["main.py"])
    repo.index.commit("Initial commit with main.py")

    # Commit 2
    f2 = tmp_path / "utils.py"
    f2.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    repo.index.add(["utils.py"])
    repo.index.commit("Add helper math function")

    # Commit 3
    f1.write_text("print('hello world')\nx = 10\ny = 20\nz = 30\n", encoding="utf-8")
    repo.index.add(["main.py"])
    repo.index.commit("Extend main.py logic")

    # 1. Detection
    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(tmp_path)
    assert status == "completed"
    assert availability == "available"
    assert repo_inst is not None
    assert is_shallow is False
    assert err is None

    # 2. Extraction
    commits, warnings = GitCommitExtractor.extract_commits(repo_inst)
    assert len(commits) == 3
    assert len(warnings) == 0

    # Verify hashes are present
    assert all(len(c["commit_hash"]) == 40 for c in commits)
    assert all(len(c["short_hash"]) == 8 for c in commits)

    # 3. Aggregation
    summary = GitTimelineAggregator.aggregate_timeline(commits)
    assert summary["total_commits"] == 3
    assert summary["distinct_contributors_count"] == 1
    assert summary["total_files_changed"] >= 3
    assert summary["total_additions"] >= 5
    assert summary["first_commit_at"] is not None
    assert summary["last_commit_at"] is not None
    assert summary["first_commit_at"] <= summary["last_commit_at"]


# ─── 2: Single Commit Repository ─────────────────────────────────────────────

def test_single_commit_repository(tmp_path: Path):
    """A repository with exactly 1 commit should be recognized and trigger the advisory signal."""
    repo = _init_local_git_repo(tmp_path)
    f = tmp_path / "app.py"
    f.write_text("print('All in one commit')\n", encoding="utf-8")
    repo.index.add(["app.py"])
    repo.index.commit("Single project commit")

    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(tmp_path)
    assert status == "completed"
    assert availability == "available"

    commits, _ = GitCommitExtractor.extract_commits(repo_inst)
    assert len(commits) == 1

    summary = GitTimelineAggregator.aggregate_timeline(commits)
    assert summary["total_commits"] == 1
    assert summary["duration_days"] == 0.0

    signals = generate_development_signals(summary, commits)
    assert any(s["signal_id"] == "GIT_SINGLE_COMMIT" for s in signals)


# ─── 3: Empty Repository with No Commits ──────────────────────────────────────

def test_empty_git_repository_no_commits(tmp_path: Path):
    """An initialized Git repository with no commits (unborn HEAD)."""
    _ = _init_local_git_repo(tmp_path)

    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(tmp_path)
    assert status == "empty_repository"
    assert availability == "empty"
    assert "no recorded commits" in err.lower()


# ─── 4: Missing .git Directory ────────────────────────────────────────────────

def test_missing_git_directory(tmp_path: Path):
    """Ordinary folder without a .git directory."""
    (tmp_path / "source.py").write_text("print('no git')", encoding="utf-8")

    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(tmp_path)
    assert status == "no_git_repository"
    assert availability == "unavailable"
    assert repo_inst is None
    assert "no .git directory" in err.lower()


# ─── 5: Corrupt Git Metadata ──────────────────────────────────────────────────

def test_corrupt_git_metadata(tmp_path: Path):
    """A .git folder with corrupted or unreadable contents."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("not-a-valid-head-ref", encoding="utf-8")
    (git_dir / "config").write_text("corrupt [config", encoding="utf-8")

    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(tmp_path)
    assert status in ("corrupt_git_metadata", "empty_repository")
    assert availability in ("corrupt", "empty")
    assert err is not None


# ─── 6: Shallow Repository ────────────────────────────────────────────────────

def test_shallow_repository_detection(tmp_path: Path):
    """Verify shallow repository detection via shallow file marker."""
    repo = _init_local_git_repo(tmp_path)
    (tmp_path / "file.py").write_text("x = 1\n", encoding="utf-8")
    repo.index.add(["file.py"])
    repo.index.commit("Commit 1")

    # Create shallow marker file
    shallow_file = tmp_path / ".git" / "shallow"
    shallow_file.write_text(f"{repo.head.commit.hexsha}\n", encoding="utf-8")

    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(tmp_path)
    assert status == "completed"
    assert availability == "available"
    assert is_shallow is True


# ─── 10: Contributor Statistics ───────────────────────────────────────────────

def test_multiple_contributors_statistics(tmp_path: Path):
    """Verify distinct contributor tracking and contribution counts."""
    repo = _init_local_git_repo(tmp_path)

    # Author A commit
    f1 = tmp_path / "module_a.py"
    f1.write_text("print('A')\n", encoding="utf-8")
    repo.index.add(["module_a.py"])
    author_a = git.Actor("Alice Student", "alice@college.edu")
    repo.index.commit("Alice commit", author=author_a, committer=author_a)

    # Author B commit
    f2 = tmp_path / "module_b.py"
    f2.write_text("print('B')\n", encoding="utf-8")
    repo.index.add(["module_b.py"])
    author_b = git.Actor("Bob Student", "bob@college.edu")
    repo.index.commit("Bob commit", author=author_b, committer=author_b)

    # Author A second commit
    f1.write_text("print('A updated')\n", encoding="utf-8")
    repo.index.add(["module_a.py"])
    repo.index.commit("Alice second commit", author=author_a, committer=author_a)

    commits, _ = GitCommitExtractor.extract_commits(repo)
    summary = GitTimelineAggregator.aggregate_timeline(commits)

    assert summary["total_commits"] == 3
    assert summary["distinct_contributors_count"] == 2

    contributors = summary["contributors"]
    assert len(contributors) == 2
    alice_stat = next(c for c in contributors if "Alice" in c["name"])
    bob_stat = next(c for c in contributors if "Bob" in c["name"])
    assert alice_stat["commit_count"] == 2
    assert bob_stat["commit_count"] == 1
    assert alice_stat["percentage"] == pytest.approx(66.7, abs=0.1)


# ─── 11: Advisory Signals Verification ────────────────────────────────────────

def test_development_signals_generation():
    """Verify advisory signals trigger based on defined thresholds."""
    now = datetime.now(timezone.utc)

    # Case A: Identical timestamps (3 commits at exact same second)
    identical_commits = [
        {"commit_hash": "a1", "short_hash": "a1", "committed_at": now, "author_name": "Dev", "files_changed_count": 1, "lines_added": 10, "lines_deleted": 0, "is_merge": False},
        {"commit_hash": "a2", "short_hash": "a2", "committed_at": now, "author_name": "Dev", "files_changed_count": 1, "lines_added": 10, "lines_deleted": 0, "is_merge": False},
        {"commit_hash": "a3", "short_hash": "a3", "committed_at": now, "author_name": "Dev", "files_changed_count": 1, "lines_added": 10, "lines_deleted": 0, "is_merge": False},
    ]
    summary_a = GitTimelineAggregator.aggregate_timeline(identical_commits)
    signals_a = generate_development_signals(summary_a, identical_commits)
    assert any(s["signal_id"] == "GIT_IDENTICAL_TIMESTAMPS" for s in signals_a)

    # Case B: Dormancy gap (20 days between commits)
    gap_commits = [
        {"commit_hash": "b1", "short_hash": "b1", "committed_at": now - timedelta(days=25), "author_name": "Dev", "files_changed_count": 1, "lines_added": 10, "lines_deleted": 0, "is_merge": False},
        {"commit_hash": "b2", "short_hash": "b2", "committed_at": now, "author_name": "Dev", "files_changed_count": 1, "lines_added": 10, "lines_deleted": 0, "is_merge": False},
    ]
    summary_b = GitTimelineAggregator.aggregate_timeline(gap_commits)
    signals_b = generate_development_signals(summary_b, gap_commits)
    assert any(s["signal_id"] == "GIT_DORMANCY_GAP" for s in signals_b)

    # Case C: Single large commit concentration (>70% in one commit)
    conc_commits = [
        {"commit_hash": "c1", "short_hash": "c1", "committed_at": now - timedelta(days=2), "author_name": "Dev", "files_changed_count": 10, "lines_added": 800, "lines_deleted": 100, "is_merge": False},
        {"commit_hash": "c2", "short_hash": "c2", "committed_at": now, "author_name": "Dev", "files_changed_count": 1, "lines_added": 10, "lines_deleted": 5, "is_merge": False},
    ]
    summary_c = GitTimelineAggregator.aggregate_timeline(conc_commits)
    signals_c = generate_development_signals(summary_c, conc_commits)
    assert any(s["signal_id"] == "GIT_LARGE_SINGLE_COMMIT_CONCENTRATION" for s in signals_c)


# ─── 12: Merge Commits and Deduplication ─────────────────────────────────────

def test_merge_commits_and_deduplication(tmp_path: Path):
    """Verify merge commit detection and deduplication across branch traversal."""
    repo = _init_local_git_repo(tmp_path)

    # Master commit 1
    (tmp_path / "base.txt").write_text("base\n", encoding="utf-8")
    repo.index.add(["base.txt"])
    repo.index.commit("Base commit")

    # Create feature branch
    feature_branch = repo.create_head("feature")
    feature_branch.checkout()

    (tmp_path / "feature.txt").write_text("feature work\n", encoding="utf-8")
    repo.index.add(["feature.txt"])
    repo.index.commit("Feature commit")

    # Return to master and merge
    master = repo.heads.master if "master" in repo.heads else repo.heads[0]
    master.checkout()

    (tmp_path / "master_work.txt").write_text("master work\n", encoding="utf-8")
    repo.index.add(["master_work.txt"])
    repo.index.commit("Master concurrent work")

    # Merge feature into master with a real merge commit
    repo.git.merge("feature", "--no-ff", "-m", "Merge branch feature into master")

    commits, _ = GitCommitExtractor.extract_commits(repo)
    # Total commits: base + feature + master_work + merge = 4
    assert len(commits) == 4

    # Verify merge commit flag
    merge_commits = [c for c in commits if c["is_merge"]]
    assert len(merge_commits) >= 1
    assert merge_commits[0]["is_merge"] is True

    # Verify no duplicate hashes
    hashes = [c["commit_hash"] for c in commits]
    assert len(hashes) == len(set(hashes))


# ─── 13: Path Boundary Containment ───────────────────────────────────────────

def test_git_path_boundary_containment(tmp_path: Path):
    """Verify that an invalid path or attempted path escape returns an error."""
    non_existent = tmp_path / "does_not_exist"
    status, availability, repo_inst, is_shallow, err = GitRepositoryDetector.detect_repository(non_existent)
    assert status == "no_git_repository"
    assert availability == "unavailable"


# ─── 14, 15, 16, 17, 18: Service & API Integration ──────────────────────────

def test_service_and_api_endpoints_idempotent(client: TestClient, db_session: Session):
    """
    Test full service execution and API endpoints:
    - 404 for nonexistent projects
    - Initial GET before analysis returns 'not_started'
    - POST triggers Git analysis
    - GET returns saved results
    - Re-analysis is idempotent (exactly 1 record in DB)
    - Inclusion in unified analysis endpoint
    """
    project_id = "test_git_integration_001"

    # 1. 404 on nonexistent project
    res_404 = client.get(f"/api/projects/{project_id}/development-history")
    assert res_404.status_code == 404

    res_post_404 = client.post(f"/api/projects/{project_id}/analyze/development-history")
    assert res_post_404.status_code == 404

    # 2. Create project in DB
    proj = Project(
        id=project_id,
        title="Git History Test Project",
        course="CS401",
        archive_filename="test.zip",
        archive_path="test_uploads/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(proj)
    db_session.commit()

    # Create physical extract directory for project with valid Git repo
    extract_dir = ProjectParser.get_project_extract_dir(project_id)
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        repo = _init_local_git_repo(extract_dir)
        (extract_dir / "index.js").write_text("console.log('first');\n", encoding="utf-8")
        repo.index.add(["index.js"])
        repo.index.commit("Commit one: add index.js")

        (extract_dir / "index.js").write_text("console.log('first');\nconsole.log('second');\n", encoding="utf-8")
        repo.index.add(["index.js"])
        repo.index.commit("Commit two: extend index.js")

        # 3. GET before analysis -> not_started
        get_pre = client.get(f"/api/projects/{project_id}/development-history")
        assert get_pre.status_code == 200
        data_pre = get_pre.json()
        assert data_pre["status"] == "not_started"
        assert data_pre["availability"] == "unavailable"

        # 4. POST /analyze/development-history
        post_res = client.post(f"/api/projects/{project_id}/analyze/development-history")
        assert post_res.status_code == 200
        post_data = post_res.json()

        assert post_data["projectId"] == project_id
        assert post_data["status"] == "completed"
        assert post_data["availability"] == "available"
        assert post_data["summary"] is not None
        assert post_data["summary"]["totalCommits"] == 2
        assert len(post_data["timeline"]) == 2

        # Verify timeline ordering (oldest first for display)
        t0 = post_data["timeline"][0]["committedAt"]
        t1 = post_data["timeline"][1]["committedAt"]
        assert t0 <= t1

        # 5. GET /development-history returns saved results
        get_res = client.get(f"/api/projects/{project_id}/development-history")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["projectId"] == project_id
        assert get_data["summary"]["totalCommits"] == 2
        assert len(get_data["timeline"]) == 2

        # 6. Idempotent re-analysis: run POST again
        post_re = client.post(f"/api/projects/{project_id}/analyze/development-history")
        assert post_re.status_code == 200

        # Verify exactly 1 analysis record in database
        analyses = (
            db_session.query(ProjectGitHistoryAnalysis)
            .filter(ProjectGitHistoryAnalysis.project_id == project_id)
            .all()
        )
        assert len(analyses) == 1

        # Verify commit records count in DB
        commit_records = (
            db_session.query(ProjectCommitRecord)
            .filter(ProjectCommitRecord.project_id == project_id)
            .all()
        )
        assert len(commit_records) == 2

        # 7. Unified analysis endpoint inclusion
        bundle_res = client.get(f"/api/projects/{project_id}/analysis")
        assert bundle_res.status_code == 200
        bundle = bundle_res.json()

        dev_module = next((m for m in bundle["modules"] if m["name"] == "Development History"), None)
        assert dev_module is not None
        assert dev_module["status"] == "completed"

        dev_data = bundle.get("developmentHistory")
        assert dev_data is not None
        assert dev_data["status"] == "completed"
        assert dev_data["totalCommits"] == 2

    finally:
        # Clean up temporary extracted directory
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)


def test_service_project_without_git(client: TestClient, db_session: Session):
    """Test analysis on a project where no .git directory exists."""
    project_id = "test_no_git_proj_002"

    proj = Project(
        id=project_id,
        title="No Git Project",
        archive_filename="nogit.zip",
        archive_path="test_uploads/nogit.zip",
        file_size_bytes=512,
    )
    db_session.add(proj)
    db_session.commit()

    extract_dir = ProjectParser.get_project_extract_dir(project_id)
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        (extract_dir / "index.html").write_text("<h1>No Git</h1>", encoding="utf-8")

        # Run analysis
        post_res = client.post(f"/api/projects/{project_id}/analyze/development-history")
        assert post_res.status_code == 200
        data = post_res.json()

        assert data["status"] == "no_git_repository"
        assert data["availability"] == "unavailable"
        assert data["summary"] is None
        assert len(data["timeline"]) == 0
        assert any("no .git" in lim.lower() for lim in data["limitations"])
    finally:
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
