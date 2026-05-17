"""
Tests for models.py - Pydantic data models
"""
import pytest
from pydantic import ValidationError
from models import (
    AnalyzeRequest,
    AffectedFile,
    ImpactReport,
    ScanRequest,
    FragileFile,
    RepoHealthReport
)


def test_analyze_request_valid():
    """Test AnalyzeRequest with valid data"""
    request = AnalyzeRequest(
        repo_url="https://github.com/owner/repo",
        pr_number=123
    )
    assert request.repo_url == "https://github.com/owner/repo"
    assert request.pr_number == 123


def test_analyze_request_invalid_pr_number():
    """Test AnalyzeRequest rejects invalid PR numbers"""
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            repo_url="https://github.com/owner/repo",
            pr_number=0
        )
    
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            repo_url="https://github.com/owner/repo",
            pr_number=-1
        )


def test_affected_file_valid():
    """Test AffectedFile model"""
    file = AffectedFile(
        path="src/main.py",
        impact="high",
        reason="Core application logic"
    )
    assert file.path == "src/main.py"
    assert file.impact == "high"
    assert file.reason == "Core application logic"


def test_impact_report_valid():
    """Test ImpactReport with all fields"""
    report = ImpactReport(
        pr_title="Test PR",
        pr_number=123,
        repo_name="test/repo",
        affected_files=[
            AffectedFile(path="test.py", impact="low", reason="Test file")
        ],
        stale_tests=["test_old.py"],
        stale_docs=["README.md"],
        risk_score="medium",
        summary="Test summary"
    )
    assert report.pr_number == 123
    assert report.risk_score == "medium"
    assert len(report.affected_files) == 1
    assert len(report.stale_tests) == 1


def test_impact_report_empty_lists():
    """Test ImpactReport with empty lists"""
    report = ImpactReport(
        pr_title="Test PR",
        pr_number=1,
        repo_name="test/repo",
        affected_files=[],
        stale_tests=[],
        stale_docs=[],
        risk_score="low",
        summary="No changes"
    )
    assert len(report.affected_files) == 0
    assert len(report.stale_tests) == 0
    assert len(report.stale_docs) == 0


def test_scan_request_valid():
    """Test ScanRequest with valid URL"""
    request = ScanRequest(repo_url="https://github.com/owner/repo")
    assert request.repo_url == "https://github.com/owner/repo"


def test_scan_request_missing_url():
    """Test ScanRequest requires URL"""
    with pytest.raises(ValidationError):
        ScanRequest()


def test_fragile_file_valid():
    """Test FragileFile model"""
    file = FragileFile(
        path="src/core.py",
        reason="Complex state management",
        risk="high"
    )
    assert file.path == "src/core.py"
    assert file.risk == "high"
    assert file.reason == "Complex state management"


def test_repo_health_report_valid():
    """Test RepoHealthReport with all fields"""
    report = RepoHealthReport(
        repo_name="test/repo",
        language="Python",
        stars=100,
        health_score="A",
        health_summary="Excellent codebase",
        source_files_count=50,
        test_files_count=45,
        doc_files_count=10,
        total_files=105,
        fragile_files=[
            FragileFile(path="core.py", reason="Complex", risk="high")
        ],
        untested_modules=["utils.py"],
        top_risks=["Risk 1", "Risk 2"],
        stale_docs=["old.md"],
        recommendations=["Add tests", "Update docs"]
    )
    assert report.health_score == "A"
    assert report.source_files_count == 50
    assert report.test_files_count == 45
    assert len(report.fragile_files) == 1
    assert len(report.recommendations) == 2


def test_repo_health_report_grade_validation():
    """Test health score accepts valid grades"""
    for grade in ["A", "B", "C", "D"]:
        report = RepoHealthReport(
            repo_name="test/repo",
            language="Python",
            stars=0,
            health_score=grade,
            health_summary="Test",
            source_files_count=1,
            test_files_count=0,
            doc_files_count=0,
            total_files=1,
            fragile_files=[],
            untested_modules=[],
            top_risks=[],
            stale_docs=[],
            recommendations=[]
        )
        assert report.health_score == grade


def test_model_json_serialization():
    """Test models can be serialized to JSON"""
    report = ImpactReport(
        pr_title="Test",
        pr_number=1,
        repo_name="test/repo",
        affected_files=[],
        stale_tests=[],
        stale_docs=[],
        risk_score="low",
        summary="Test"
    )
    json_data = report.model_dump()
    assert isinstance(json_data, dict)
    assert json_data["pr_number"] == 1
    assert json_data["risk_score"] == "low"

# Made with Bob
