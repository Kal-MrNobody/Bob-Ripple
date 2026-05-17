from pydantic import BaseModel, Field
from typing import List, Literal


class AnalyzeRequest(BaseModel):
    """Request model for PR analysis"""
    repo_url: str = Field(..., description="GitHub repository URL (e.g., https://github.com/owner/repo)")
    pr_number: int = Field(..., description="Pull request number", gt=0)


class AffectedFile(BaseModel):
    """Model for a file affected by the PR"""
    path: str = Field(..., description="File path relative to repository root")
    changes: int = Field(..., description="Number of lines changed")
    impact: Literal["high", "medium", "low"] = Field(..., description="Impact level of changes")
    reason: str = Field(..., description="Explanation of why this file is impacted")


class ImpactReport(BaseModel):
    """Complete impact analysis report for a PR"""
    pr_number: int = Field(..., description="Pull request number")
    repo_name: str = Field(..., description="Repository name")
    pr_title: str = Field(..., description="Pull request title")
    affected_files: List[AffectedFile] = Field(default_factory=list, description="List of affected files")
    risk_score: Literal["high", "medium", "low"] = Field(..., description="Overall risk assessment")
    stale_tests: List[str] = Field(default_factory=list, description="Test files that may need updates")
    stale_docs: List[str] = Field(default_factory=list, description="Documentation files that may need updates")
    summary: str = Field(..., description="Executive summary of the impact analysis")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "Bob Ripple API"


class ScanRequest(BaseModel):
    """Request model for repository health scan"""
    repo_url: str = Field(..., description="GitHub repository URL (e.g., https://github.com/owner/repo)")


class FragileFile(BaseModel):
    """Model for a fragile file in the repository"""
    path: str = Field(..., description="File path")
    reason: str = Field(..., description="Reason why this file is fragile")
    risk: Literal["high", "medium", "low"] = Field(..., description="Risk level")


class RepoHealthReport(BaseModel):
    """Complete repository health assessment report"""
    repo_name: str = Field(..., description="Repository name")
    repo_description: str = Field(..., description="Repository description")
    language: str = Field(..., description="Primary programming language")
    stars: int = Field(..., description="Number of stars")
    total_files: int = Field(..., description="Total number of files analyzed")
    source_files_count: int = Field(..., description="Number of source files")
    test_files_count: int = Field(..., description="Number of test files")
    doc_files_count: int = Field(..., description="Number of documentation files")
    health_score: Literal["A", "B", "C", "D", "unknown"] = Field(..., description="Overall health grade")
    health_summary: str = Field(..., description="Summary of repository health")
    untested_modules: List[str] = Field(default_factory=list, description="Source files without tests")
    fragile_files: List[FragileFile] = Field(default_factory=list, description="Files that may be fragile")
    stale_docs: List[str] = Field(default_factory=list, description="Documentation that may be outdated")
    top_risks: List[str] = Field(default_factory=list, description="Top 3 risks")
    recommendations: List[str] = Field(default_factory=list, description="Top 3 recommendations")

# Made with Bob
