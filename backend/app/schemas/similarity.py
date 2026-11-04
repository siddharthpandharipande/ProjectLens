from datetime import datetime
from typing import List, Optional, Tuple, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class FileSimilarityMatchItem(BaseModel):
    currentFile: str = Field(..., description="Relative path in current project")
    matchedFile: str = Field(..., description="Relative path in matched cohort project")
    currentLines: Tuple[int, int] = Field(default=(1, 1), description="Start and end line in current file")
    matchedLines: Tuple[int, int] = Field(default=(1, 1), description="Start and end line in matched file")
    similarityPercent: float = Field(default=0.0, description="Overall similarity percentage for file pair")
    identicalStatements: int = Field(default=0, description="Count of identical statement/token spans")
    currentSnippet: str = Field(default="", description="Source preview snippet from current file")
    matchedSnippet: str = Field(default="", description="Source preview snippet from matched file")
    tokenSimilarity: Optional[float] = Field(None, description="Token-level similarity score")
    structuralSimilarity: Optional[float] = Field(None, description="Syntax-tree / AST structural similarity score")
    semanticSimilarity: Optional[float] = Field(None, description="Semantic embedding similarity score")
    comparisonMethod: str = Field(default="token+ast", description="Methods applied to compare this file pair")

    model_config = ConfigDict(populate_by_name=True)


class ProjectSimilarityMatchItem(BaseModel):
    matchedProjectId: str = Field(..., description="ID of matched cohort project")
    matchedProjectTitle: str = Field(default="Untitled Project", description="Title of matched cohort project")
    overallSimilarity: float = Field(default=0.0, description="Cohort similarity signal percentage (0-100)")
    similarityCategory: str = Field(default="minimal", description="Categorization: minimal, low, moderate, high")
    tokenSimilarity: Optional[float] = Field(None, description="Project-level token similarity")
    structuralSimilarity: Optional[float] = Field(None, description="Project-level AST/syntax tree similarity")
    semanticSimilarity: Optional[float] = Field(None, description="Project-level semantic embedding similarity")
    sourceCoveragePct: float = Field(default=0.0, description="Proportion of current project represented by matches")
    matchedCoveragePct: float = Field(default=0.0, description="Proportion of matched project represented by matches")
    identicalStatements: int = Field(default=0, description="Total identical statements found")
    matchedFilesCount: int = Field(default=0, description="Number of matching file pairs")
    totalComparedFiles: int = Field(default=0, description="Total comparable files evaluated")
    strongestFileMatches: List[FileSimilarityMatchItem] = Field(default_factory=list, description="Top file-level matches with evidence")

    model_config = ConfigDict(populate_by_name=True)


class ProjectSimilarityResponse(BaseModel):
    projectId: str = Field(..., description="Analyzed project identifier")
    status: str = Field(default="completed", description="Status of similarity analysis")
    overallSimilarity: float = Field(default=0.0, description="Highest similarity signal across cohort submissions")
    similarityCategory: str = Field(default="minimal", description="Highest similarity tier")
    advisoryNote: str = Field(
        default="Advisory evidence only. Similarity signals do not constitute proof of academic misconduct.",
        description="Faculty advisory guidance disclaimer",
    )
    comparedProjectsCount: int = Field(default=0, description="Number of eligible cohort projects compared")
    comparedFilesCount: int = Field(default=0, description="Total source files compared")
    scoringVersion: str = Field(default="v1.0-hierarchical-ast-tokens", description="Rules and scoring version")
    methodsUsed: List[str] = Field(default_factory=list, description="Active comparison methods")
    limitations: List[str] = Field(default_factory=list, description="Language and parser limitations")
    matches: List[ProjectSimilarityMatchItem] = Field(default_factory=list, description="Ranked list of cohort matches")
    createdAt: datetime = Field(..., description="Timestamp when analysis was created")
    updatedAt: datetime = Field(..., description="Timestamp when analysis was last refreshed")

    model_config = ConfigDict(populate_by_name=True)
