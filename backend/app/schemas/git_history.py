from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CommitRecordSchema(BaseModel):
    commit_hash: str = Field(..., alias="commitHash")
    short_hash: str = Field(..., alias="shortHash")
    committed_at: datetime = Field(..., alias="committedAt")
    author_name: str = Field("Unknown", alias="authorName")
    author_email: str = Field("", alias="authorEmail")
    subject: str = Field("", alias="subject")
    files_changed_count: int = Field(0, alias="filesChangedCount")
    lines_added: int = Field(0, alias="linesAdded")
    lines_deleted: int = Field(0, alias="linesDeleted")
    is_merge: bool = Field(False, alias="isMerge")
    changed_files: List[str] = Field(default_factory=list, alias="changedFiles")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ContributorStatSchema(BaseModel):
    name: str
    email: str = ""
    commit_count: int = Field(0, alias="commitCount")
    additions: int = 0
    deletions: int = 0
    percentage: float = 0.0

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class GitFindingSchema(BaseModel):
    id: Optional[int] = None
    signal_id: str = Field(..., alias="signalId")
    title: str
    severity: str  # high, medium, low, advisory, info
    category: str  # commit_concentration, timestamp_anomaly, history_duration, dormancy_gap, contributor_distribution
    explanation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    faculty_guidance: Optional[str] = Field(None, alias="facultyGuidance")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class GitHistorySummarySchema(BaseModel):
    total_commits: int = Field(0, alias="totalCommits")
    distinct_contributors_count: int = Field(0, alias="distinctContributorsCount")
    first_commit_at: Optional[datetime] = Field(None, alias="firstCommitAt")
    last_commit_at: Optional[datetime] = Field(None, alias="lastCommitAt")
    duration_days: float = Field(0.0, alias="durationDays")
    total_files_changed: int = Field(0, alias="totalFilesChanged")
    total_additions: int = Field(0, alias="totalAdditions")
    total_deletions: int = Field(0, alias="totalDeletions")
    avg_time_between_commits_hours: Optional[float] = Field(None, alias="avgTimeBetweenCommitsHours")
    median_time_between_commits_hours: Optional[float] = Field(None, alias="medianTimeBetweenCommitsHours")
    largest_commit_share_percent: Optional[float] = Field(None, alias="largestCommitSharePercent")
    top_3_commit_share_percent: Optional[float] = Field(None, alias="top3CommitSharePercent")
    activity_by_day: Dict[str, int] = Field(default_factory=dict, alias="activityByDay")
    activity_by_weekday: Dict[str, int] = Field(default_factory=dict, alias="activityByWeekday")
    size_distribution: Dict[str, int] = Field(default_factory=dict, alias="sizeDistribution")
    contributors: List[ContributorStatSchema] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class GitHistoryResponse(BaseModel):
    project_id: str = Field(..., alias="projectId")
    status: str  # completed, no_git_repository, empty_repository, corrupt_git_metadata, limit_exceeded, error, not_started
    availability: str = Field("available", alias="availability")  # available, unavailable, empty, corrupt
    is_shallow: bool = Field(False, alias="isShallow")
    analysis_version: str = Field("v1.0-git-analysis", alias="analysisVersion")
    advisory_note: str = Field(
        "Advisory development cadence and commit velocity findings. "
        "Git metadata reflects repository history as committed and cannot independently prove work authorship or timing.",
        alias="advisoryNote",
    )
    summary: Optional[GitHistorySummarySchema] = None
    timeline: List[CommitRecordSchema] = Field(default_factory=list)
    findings: List[GitFindingSchema] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )
