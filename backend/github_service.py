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

# Made with Bob
