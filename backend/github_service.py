import os
import httpx
from typing import Dict, Any, Tuple, List
from fastapi import HTTPException


def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """
    Parse GitHub repository URL to extract owner and repo name.
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/owner/repo or owner/repo)
        
    Returns:
        Tuple of (owner, repo)
        
    Raises:
        ValueError: If URL format is invalid
    """
    # Remove trailing slashes and .git extension
    repo_url = repo_url.rstrip("/").replace(".git", "")
    
    # Handle both full URLs and owner/repo format
    if "github.com/" in repo_url:
        # Extract owner and repo from full URL
        parts = repo_url.split("github.com/")[-1].split("/")
    else:
        # Assume it's already in owner/repo format
        parts = repo_url.split("/")
    
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}. Expected format: https://github.com/owner/repo or owner/repo")
    
    return parts[0], parts[1]


async def get_pr_data(repo_url: str, pr_number: int, token: str) -> Dict[str, Any]:
    """
    Fetch pull request metadata from GitHub API.
    
    Args:
        repo_url: GitHub repository URL
        pr_number: Pull request number
        token: GitHub personal access token
        
    Returns:
        Dictionary containing:
        - title: PR title
        - description: PR body/description
        - base_branch: Target branch
        - head_branch: Source branch
        - changed_files_count: Number of files changed
        
    Raises:
        HTTPException: If GitHub API returns error
    """
    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}" if token else ""
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            return {
                "title": data.get("title", ""),
                "description": data.get("body", ""),
                "base_branch": data.get("base", {}).get("ref", ""),
                "head_branch": data.get("head", {}).get("ref", ""),
                "changed_files_count": data.get("changed_files", 0),
                "owner": owner,
                "repo": repo
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Pull request #{pr_number} not found in repository {owner}/{repo}. Please verify the PR number and repository URL."
                )
            elif e.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="GitHub authentication failed. Please check your GITHUB_TOKEN in the .env file."
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"GitHub API error: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to GitHub API: {str(e)}"
            )


async def get_pr_diff(repo_url: str, pr_number: int, token: str) -> Tuple[str, List[str]]:
    """
    Fetch pull request diff and changed file paths from GitHub API.
    
    Args:
        repo_url: GitHub repository URL
        pr_number: Pull request number
        token: GitHub personal access token
        
    Returns:
        Tuple of (full_diff_string, list_of_changed_file_paths)
        Diff is truncated to 8000 chars if longer
        
    Raises:
        HTTPException: If GitHub API returns error
    """
    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # First, get the list of changed files
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}" if token else ""
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # Get changed files list
            files_response = await client.get(files_url, headers=headers, timeout=30.0)
            files_response.raise_for_status()
            files_data = files_response.json()
            
            # Extract file paths
            changed_files = [file["filename"] for file in files_data]
            
            # Get the diff
            diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            diff_headers = {
                "Accept": "application/vnd.github.v3.diff",
                "Authorization": f"token {token}" if token else ""
            }
            
            diff_response = await client.get(diff_url, headers=diff_headers, timeout=30.0)
            diff_response.raise_for_status()
            full_diff = diff_response.text
            
            # Truncate diff if too long (keep first 8000 chars)
            if len(full_diff) > 8000:
                full_diff = full_diff[:8000] + "\n... (diff truncated to 8000 chars to avoid token limits)"
            
            return full_diff, changed_files
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Pull request #{pr_number} not found in repository {owner}/{repo}. Please verify the PR number and repository URL."
                )
            elif e.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="GitHub authentication failed. Please check your GITHUB_TOKEN in the .env file."
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"GitHub API error: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to GitHub API: {str(e)}"
            )


async def get_repo_structure(repo_url: str, token: str) -> Dict[str, Any]:
    """
    Fetch repository structure and metadata from GitHub API.
    
    Args:
        repo_url: GitHub repository URL
        token: GitHub personal access token
        
    Returns:
        Dictionary containing:
        - source_files: List of source code files
        - test_files: List of test files
        - doc_files: List of documentation files
        - metadata: Repository metadata
        - total_files: Total number of files
        
    Raises:
        HTTPException: If GitHub API returns error
    """
    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}" if token else ""
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            # Get repository metadata
            repo_url_api = f"https://api.github.com/repos/{owner}/{repo}"
            repo_response = await client.get(repo_url_api, headers=headers, timeout=30.0)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            
            metadata = {
                "name": repo_data.get("full_name", f"{owner}/{repo}"),
                "description": repo_data.get("description", ""),
                "language": repo_data.get("language", "Unknown"),
                "stargazers_count": repo_data.get("stargazers_count", 0),
                "forks_count": repo_data.get("forks_count", 0)
            }
            
            # Get repository tree structure
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
            tree_response = await client.get(tree_url, headers=headers, timeout=30.0)
            tree_response.raise_for_status()
            tree_data = tree_response.json()
            
            # Extract ALL file paths from tree
            all_files = [item["path"] for item in tree_data.get("tree", []) if item["type"] == "blob"]
            total_files_count = len(all_files)
            
            # Categorize ALL files first
            source_extensions = {'.py', '.js', '.ts', '.go', '.java', '.rs', '.cpp',
                               '.c', '.cs', '.rb', '.php', '.swift', '.kt'}
            test_keywords = ['test', 'spec', '__test__', 'tests/']
            doc_extensions = {'.md', '.rst', '.txt'}
            doc_prefixes = ['docs/', 'doc/', 'documentation/']
            
            source_files = []
            test_files = []
            doc_files = []
            
            # Classify all files
            for file_path in all_files:
                # Get file extension
                ext = os.path.splitext(file_path)[1].lower()
                path_lower = file_path.lower()
                
                # Check if it's a test file (test check first)
                if ext in source_extensions and any(keyword in path_lower for keyword in test_keywords):
                    test_files.append(file_path)
                # Check if it's a source file (not a test)
                elif ext in source_extensions:
                    source_files.append(file_path)
                # Check if it's a doc file
                elif ext in doc_extensions or any(file_path.startswith(prefix) for prefix in doc_prefixes):
                    doc_files.append(file_path)
            
            # Sort source files by importance before capping
            def source_file_priority(path):
                """Return priority score for source files (lower = higher priority)"""
                path_lower = path.lower()
                filename = os.path.basename(path_lower)
                depth = path.count('/')
                
                # Priority 1: Root or one level deep
                if depth <= 1:
                    priority = 0
                else:
                    priority = 100
                
                # Priority 2: NOT in docs_src/, examples/, or scripts/
                if any(path.startswith(folder) for folder in ['docs_src/', 'examples/', 'scripts/']):
                    priority += 200
                
                # Priority 3: Important file names
                important_keywords = ['main', 'app', 'core', 'api', 'router', 'model', 'service', 'util', 'config', 'auth']
                if any(keyword in filename for keyword in important_keywords):
                    priority -= 50
                
                return priority
            
            # Sort test files to prioritize test_ prefix
            def test_file_priority(path):
                """Return priority score for test files (lower = higher priority)"""
                filename = os.path.basename(path.lower())
                return 0 if filename.startswith('test_') else 1
            
            # Apply sorting
            source_files.sort(key=source_file_priority)
            test_files.sort(key=test_file_priority)
            
            # Cap each list independently to ensure balanced sampling
            source_files = source_files[:150]
            test_files = test_files[:50]
            doc_files = doc_files[:100]
            
            return {
                "source_files": source_files,
                "test_files": test_files,
                "doc_files": doc_files,
                "metadata": metadata,
                "total_files": total_files_count
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Repository {owner}/{repo} not found. Please verify the repository URL."
                )
            elif e.response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="GitHub authentication failed. Please check your GITHUB_TOKEN in the .env file."
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"GitHub API error: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to GitHub API: {str(e)}"
            )

# Made with Bob
