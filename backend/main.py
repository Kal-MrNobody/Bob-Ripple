from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import httpx
import os
from dotenv import load_dotenv

from models import AnalyzeRequest, ImpactReport, HealthResponse
from github_service import get_pr_data, get_pr_diff
from analyzer import GeminiAnalyzer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize analyzer
analyzer = GeminiAnalyzer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    logger.info("Starting Bob Ripple API...")
    yield
    logger.info("Shutting down Bob Ripple API...")


# Create FastAPI app
app = FastAPI(
    title="Bob Ripple API",
    description="Analyze GitHub PR impact using Google Gemini AI",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        HealthResponse with status information
    """
    return HealthResponse()


@app.post("/analyze", response_model=ImpactReport)
async def analyze_pr(request: AnalyzeRequest):
    """
    Analyze a GitHub Pull Request for impact assessment.
    
    Args:
        request: AnalyzeRequest containing repo_url and pr_number
        
    Returns:
        ImpactReport with detailed analysis
        
    Raises:
        HTTPException: If PR cannot be fetched or analyzed
    """
    try:
        logger.info(f"Analyzing PR #{request.pr_number} from {request.repo_url}")
        
        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN", "")
        
        # Fetch PR metadata
        pr_data = await get_pr_data(request.repo_url, request.pr_number, github_token)
        logger.info(f"Fetched PR data: {pr_data['changed_files_count']} files changed")
        
        # Fetch PR diff and changed files
        diff, changed_files = await get_pr_diff(request.repo_url, request.pr_number, github_token)
        logger.info(f"Fetched diff: {len(diff)} chars, {len(changed_files)} files")
        
        # Combine data for analyzer
        analysis_data = {
            **pr_data,
            "diff": diff,
            "changed_files": changed_files,
            "pr_number": request.pr_number
        }
        
        # Analyze PR impact using Gemini
        impact_report = await analyzer.analyze_pr_impact(analysis_data)
        logger.info(f"Analysis complete: Risk score = {impact_report.risk_score}")
        
        return impact_report
        
    except HTTPException:
        # Re-raise HTTPExceptions from github_service
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during analysis: {str(e)}"
        )


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        Dictionary with API details
    """
    return {
        "service": "Bob Ripple API",
        "version": "1.0.0",
        "description": "Analyze GitHub PR impact using Google Gemini AI",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
