"""
Tests for github_service.py - GitHub API integration
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from github_service import parse_repo_url, get_pr_data, get_pr_diff, get_repo_structure


def test_parse_repo_url_valid():
    """Test parsing valid GitHub URLs"""
    owner, repo = parse_repo_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"
    
    owner, repo = parse_repo_url("https://github.com/owner/repo.git")
    assert owner == "owner"
    assert repo == "repo"


def test_parse_repo_url_invalid():
    """Test parsing invalid URLs raises exception"""
    with pytest.raises(HTTPException) as exc:
        parse_repo_url("https://invalid.com/owner/repo")
    assert exc.value.status_code == 400
    
    with pytest.raises(HTTPException) as exc:
        parse_repo_url("not-a-url")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_pr_data_success():
    """Test successful PR data retrieval"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "title": "Test PR",
        "number": 123,
        "state": "open"
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await get_pr_data("owner", "repo", 123)
        
        assert result["title"] == "Test PR"
        assert result["number"] == 123


@pytest.mark.asyncio
async def test_get_pr_data_not_found():
    """Test PR not found returns 404"""
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(HTTPException) as exc:
            await get_pr_data("owner", "repo", 999)
        
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_pr_diff_success():
    """Test successful PR diff retrieval"""
    mock_files_response = Mock()
    mock_files_response.status_code = 200
    mock_files_response.json.return_value = [
        {
            "filename": "test.py",
            "patch": "@@ -1,3 +1,3 @@\n-old\n+new"
        }
    ]
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_files_response)
        
        diff, files = await get_pr_diff("owner", "repo", 123)
        
        assert "test.py" in diff
        assert "test.py" in files
        assert len(files) == 1


@pytest.mark.asyncio
async def test_get_pr_diff_truncates_large_diff():
    """Test that large diffs are truncated"""
    large_patch = "x" * 15000
    mock_files_response = Mock()
    mock_files_response.status_code = 200
    mock_files_response.json.return_value = [
        {
            "filename": "large.py",
            "patch": large_patch
        }
    ]
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_files_response)
        
        diff, files = await get_pr_diff("owner", "repo", 123)
        
        assert len(diff) <= 12000
        assert "[truncated]" in diff


@pytest.mark.asyncio
async def test_get_repo_structure_success():
    """Test successful repository structure retrieval"""
    mock_tree_response = Mock()
    mock_tree_response.status_code = 200
    mock_tree_response.json.return_value = {
        "tree": [
            {"path": "main.py", "type": "blob"},
            {"path": "test_main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": "folder", "type": "tree"}
        ]
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_tree_response)
        
        source, test, doc = await get_repo_structure("owner", "repo")
        
        assert "main.py" in source
        assert "test_main.py" in test
        assert "README.md" in doc


@pytest.mark.asyncio
async def test_get_repo_structure_caps_files():
    """Test that file lists are capped at limits"""
    # Create 200 source files
    tree_items = [{"path": f"file{i}.py", "type": "blob"} for i in range(200)]
    
    mock_tree_response = Mock()
    mock_tree_response.status_code = 200
    mock_tree_response.json.return_value = {"tree": tree_items}
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_tree_response)
        
        source, test, doc = await get_repo_structure("owner", "repo")
        
        # Should cap at 150 source files
        assert len(source) <= 150

# Made with Bob
