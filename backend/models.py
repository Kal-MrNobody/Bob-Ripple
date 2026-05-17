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

# Made with Bob
