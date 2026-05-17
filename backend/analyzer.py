import httpx
import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from models import ImpactReport, AffectedFile, FragileFile

load_dotenv()


class GeminiAnalyzer:
    """Service for analyzing PR impact using Google Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    
    def _build_analysis_prompt(self, pr_data: Dict[str, Any]) -> str:
        """
        Build a structured prompt for Gemini to analyze PR impact.
        
        Args:
            pr_data: Dictionary containing PR metadata, diff, and changed files
            
        Returns:
            Formatted prompt string
        """
        title = pr_data.get("title", "")
        description = pr_data.get("description", "")
        diff = pr_data.get("diff", "")
        changed_files = pr_data.get("changed_files", [])
        owner = pr_data.get("owner", "")
        repo = pr_data.get("repo", "")
        pr_number = pr_data.get("pr_number", 0)
        
        file_list = "\n".join([f"- {file}" for file in changed_files])
        
        prompt = f"""You are a senior software architect. Analyze this PR diff and return ONLY valid JSON, no markdown, no backticks, no explanation.

Repository: {owner}/{repo}
PR #{pr_number}: {title}
Description: {description}

Changed files:
{file_list}

PR Diff:
{diff}

Return exactly this structure:
{{
  "affected_files": [{{"path": "string", "changes": number, "impact": "high|medium|low", "reason": "string"}}],
  "stale_tests": ["string"],
  "stale_docs": ["string"],
  "risk_score": "high|medium|low",
  "summary": "string"
}}

Consider:
1. Which files are most critical to the system?
2. Are there breaking changes?
3. Which test files might need updates based on the changes?
4. Which documentation files might be outdated?
5. Overall risk level (high: breaking changes/critical files, medium: moderate impact, low: minor changes)"""
        
        return prompt
    
    async def analyze_pr_impact(self, pr_data: Dict[str, Any]) -> ImpactReport:
        """
        Analyze PR impact using Google Gemini API.
        
        Args:
            pr_data: Dictionary containing PR metadata, diff, and changed files
            
        Returns:
            ImpactReport object with analysis results
        """
        prompt = self._build_analysis_prompt(pr_data)
        
        # Build request payload
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 1,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 1024}
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        # Call Gemini API
        result = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, headers=headers, json=payload, timeout=60.0)
                response.raise_for_status()
                result = response.json()
        except Exception:
            # Handle any errors with fallback analysis
            return self._create_fallback_analysis(pr_data, "")
        
        # Process the result
        try:
            # Extract generated text from response
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse JSON response
            try:
                analysis_data = json.loads(generated_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return report with generic message
                return ImpactReport(
                    pr_number=pr_data.get("pr_number", 0),
                    repo_name=f"{pr_data.get('owner', '')}/{pr_data.get('repo', '')}",
                    pr_title=pr_data.get("title", ""),
                    affected_files=[],
                    risk_score="medium",
                    stale_tests=[],
                    stale_docs=[],
                    summary="Analysis unavailable — please try again."
                )
            
            # Build ImpactReport from parsed data
            affected_files = [
                AffectedFile(**file_data)
                for file_data in analysis_data.get("affected_files", [])
            ]
            
            return ImpactReport(
                pr_number=pr_data.get("pr_number", 0),
                repo_name=f"{pr_data.get('owner', '')}/{pr_data.get('repo', '')}",
                pr_title=pr_data.get("title", ""),
                affected_files=affected_files,
                risk_score=analysis_data.get("risk_score", "medium"),
                stale_tests=analysis_data.get("stale_tests", []),
                stale_docs=analysis_data.get("stale_docs", []),
                summary=analysis_data.get("summary", "Impact analysis completed.")
            )
            
        except KeyError:
            # Handle unexpected response structure
            return self._create_fallback_analysis(pr_data, "")
        except Exception:
            # Handle any other errors
            return self._create_fallback_analysis(pr_data, "")
    
    def _create_fallback_analysis(self, pr_data: Dict[str, Any], error_msg: str = "") -> ImpactReport:
        """
        Create a basic fallback analysis if AI parsing fails.
        
        Args:
            pr_data: Dictionary containing PR metadata, diff, and changed files
            error_msg: Optional error message (not used, kept for compatibility)
            
        Returns:
            ImpactReport with basic heuristic-based analysis
        """
        changed_files = pr_data.get("changed_files", [])
        diff = pr_data.get("diff", "")
        
        # Simple heuristic-based analysis
        affected_files = []
        stale_tests = []
        stale_docs = []
        
        for file_path in changed_files[:10]:  # Limit to first 10 files
            # Estimate changes (rough heuristic based on diff length)
            total_changes = len(diff) // max(len(changed_files), 1)
            
            # Determine impact based on file type and changes
            if total_changes > 100:
                impact = "high"
            elif total_changes > 30:
                impact = "medium"
            else:
                impact = "low"
            
            affected_files.append(AffectedFile(
                path=file_path,
                changes=total_changes,
                impact=impact,
                reason=f"Modified file with estimated {total_changes} changes"
            ))
            
            # Check for test files
            if "test" in file_path.lower() or file_path.endswith("_test.py") or file_path.endswith(".test.js"):
                stale_tests.append(file_path)
            
            # Check for doc files
            if any(ext in file_path.lower() for ext in [".md", "readme", "doc", "docs/"]):
                stale_docs.append(file_path)
        
        # Determine overall risk
        total_files = len(changed_files)
        if total_files > 20 or len(diff) > 5000:
            risk_score = "high"
        elif total_files > 5 or len(diff) > 2000:
            risk_score = "medium"
        else:
            risk_score = "low"
        
        # Always use generic error message
        summary = "Analysis unavailable — please try again."
        
        return ImpactReport(
            pr_number=pr_data.get("pr_number", 0),
            repo_name=f"{pr_data.get('owner', '')}/{pr_data.get('repo', '')}",
            pr_title=pr_data.get("title", ""),
            affected_files=affected_files,
            risk_score=risk_score,
            stale_tests=stale_tests,
            stale_docs=stale_docs,
            summary=summary
        )
    
    async def analyze_repo_health(
        self,
        source_files: List[str],
        test_files: List[str],
        doc_files: List[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze repository health using Google Gemini API.
        
        Args:
            source_files: List of source code file paths
            test_files: List of test file paths
            doc_files: List of documentation file paths
            metadata: Repository metadata
            
        Returns:
            Dictionary with health analysis results
        """
        # Build prompt
        source_list = "\n".join(source_files[:50])  # Limit to first 50 for prompt size
        test_list = "\n".join(test_files[:50])
        doc_list = "\n".join(doc_files[:50])
        
        prompt = f"""You are a senior software architect doing a repository health assessment.

Repository: {metadata.get('name', 'Unknown')}
Language: {metadata.get('language', 'Unknown')}

Source files ({len(source_files)} total):
{source_list}

Test files ({len(test_files)} total):
{test_list}

Doc files ({len(doc_files)} total):
{doc_list}

Analyze this repository structure and return ONLY valid JSON no markdown:
{{
  "health_score": "A or B or C or D",
  "health_summary": "2-3 sentence overall assessment",
  "untested_modules": ["list of source file paths with no corresponding test"],
  "fragile_files": [{{"path": "string", "reason": "string", "risk": "high|medium|low"}}],
  "stale_docs": ["list of doc files likely outdated based on structure"],
  "top_risks": ["3 specific risks in plain English"],
  "recommendations": ["3 actionable improvements"]
}}"""
        
        # Build request payload
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 1,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 1024}
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        try:
            # Call Gemini API
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, headers=headers, json=payload, timeout=60.0)
                response.raise_for_status()
                result = response.json()
            
            # Extract generated text
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Parse JSON response
            try:
                analysis_data = json.loads(generated_text)
                return analysis_data
            except json.JSONDecodeError:
                # Return default structure on parse failure
                return {
                    "health_score": "unknown",
                    "health_summary": "Analysis unavailable — please try again.",
                    "untested_modules": [],
                    "fragile_files": [],
                    "stale_docs": [],
                    "top_risks": [],
                    "recommendations": []
                }
        except Exception:
            # Return default structure on any error
            return {
                "health_score": "unknown",
                "health_summary": "Analysis unavailable — please try again.",
                "untested_modules": [],
                "fragile_files": [],
                "stale_docs": [],
                "top_risks": [],
                "recommendations": []
            }

# Made with Bob
