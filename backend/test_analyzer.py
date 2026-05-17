"""
Tests for analyzer.py - Gemini AI integration
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from analyzer import analyze_pr_impact, analyze_repo_health


@pytest.mark.asyncio
async def test_analyze_pr_impact_success():
    """Test successful PR impact analysis"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": '{"affected_files": [], "stale_tests": [], "stale_docs": [], "risk_score": "low", "summary": "Test"}'
                }]
            }
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await analyze_pr_impact(
            repo_name="test/repo",
            pr_number=1,
            pr_title="Test PR",
            diff="test diff",
            changed_files=["test.py"]
        )
        
        assert result["risk_score"] == "low"
        assert result["summary"] == "Test"
        assert isinstance(result["affected_files"], list)


@pytest.mark.asyncio
async def test_analyze_pr_impact_api_error():
    """Test PR analysis handles API errors gracefully"""
    mock_response = Mock()
    mock_response.status_code = 500
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await analyze_pr_impact(
            repo_name="test/repo",
            pr_number=1,
            pr_title="Test PR",
            diff="test diff",
            changed_files=["test.py"]
        )
        
        # Should return empty response on error
        assert result["risk_score"] == "medium"
        assert result["affected_files"] == []


@pytest.mark.asyncio
async def test_analyze_repo_health_success():
    """Test successful repository health analysis"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": '{"health_score": "A", "fragile_files": [], "untested_modules": [], "top_risks": [], "recommendations": [], "health_summary": "Great!"}'
                }]
            }
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await analyze_repo_health(
            repo_name="test/repo",
            language="Python",
            stars=100,
            source_files=["main.py"],
            test_files=["test_main.py"],
            doc_files=["README.md"]
        )
        
        assert result["health_score"] == "A"
        assert result["health_summary"] == "Great!"
        assert isinstance(result["fragile_files"], list)


@pytest.mark.asyncio
async def test_analyze_repo_health_invalid_json():
    """Test repo health analysis handles invalid JSON"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": 'invalid json'
                }]
            }
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await analyze_repo_health(
            repo_name="test/repo",
            language="Python",
            stars=100,
            source_files=["main.py"],
            test_files=[],
            doc_files=[]
        )
        
        # Should return default values on parse error
        assert result["health_score"] == "C"
        assert result["fragile_files"] == []

# Made with Bob
