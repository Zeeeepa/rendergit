"""
Web server for rendergit.

This module provides a FastAPI-based web server for rendering
GitHub repositories via a web interface.
"""

import asyncio
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Any

import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl, validator

from rendergit.core import analyze_repo, RepoAnalysisResult, MAX_DEFAULT_BYTES

# Initialize FastAPI app
app = FastAPI(
    title="rendergit",
    description="Render any git repo into a single static HTML page for humans or LLMs",
    version="0.2.0",
)

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set up templates and static files
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# In-memory cache for analysis results
# This is a simple cache that stores the results of repository analyses
# Key: task_id, Value: RepoAnalysisResult or None if still processing
analysis_cache: Dict[str, Optional[RepoAnalysisResult]] = {}

# Thread pool for running repository analyses
executor = ThreadPoolExecutor(max_workers=4)


class RepoRequest(BaseModel):
    """Model for repository analysis request."""
    repo_url: HttpUrl
    max_bytes: int = MAX_DEFAULT_BYTES
    
    @validator('repo_url')
    def validate_github_url(cls, v):
        """Validate that the URL is a GitHub repository URL."""
        if not re.match(r'https?://(www\.)?github\.com/[^/]+/[^/]+/?.*', str(v)):
            raise ValueError('URL must be a GitHub repository URL')
        return v


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page with the repository input form."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )


@app.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    repo_url: str = Form(...),
    max_bytes: int = Form(MAX_DEFAULT_BYTES)
):
    """
    Start a repository analysis task.
    
    Args:
        repo_url: URL of the GitHub repository
        max_bytes: Maximum file size to render
        
    Returns:
        Redirect to the results page
    """
    # Validate the repository URL
    if not re.match(r'https?://(www\.)?github\.com/[^/]+/[^/]+/?.*', repo_url):
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    
    # Store a placeholder in the cache
    analysis_cache[task_id] = None
    
    # Start the analysis in a background task
    background_tasks.add_task(
        analyze_repo_background,
        task_id=task_id,
        repo_url=repo_url,
        max_bytes=max_bytes
    )
    
    # Redirect to the results page
    return RedirectResponse(url=f"/results/{task_id}", status_code=303)


@app.get("/results/{task_id}", response_class=HTMLResponse)
async def results(request: Request, task_id: str):
    """
    Render the results page for a repository analysis task.
    
    Args:
        task_id: ID of the analysis task
        
    Returns:
        HTML response with the results or a loading page
    """
    # Check if the task exists
    if task_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get the analysis result
    result = analysis_cache[task_id]
    
    # If the analysis is still running, show a loading page
    if result is None:
        return templates.TemplateResponse(
            "loading.html",
            {
                "request": request,
                "task_id": task_id
            }
        )
    
    # If there was an error, show an error page
    if result.error:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": result.error,
                "repo_url": result.repo_url
            }
        )
    
    # Return the rendered HTML
    return HTMLResponse(content=result.html_content)


@app.get("/api/status/{task_id}")
async def task_status(task_id: str):
    """
    Get the status of a repository analysis task.
    
    Args:
        task_id: ID of the analysis task
        
    Returns:
        JSON response with the task status
    """
    # Check if the task exists
    if task_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get the analysis result
    result = analysis_cache[task_id]
    
    # Return the status
    if result is None:
        return {"status": "processing"}
    elif result.error:
        return {"status": "error", "error": result.error}
    else:
        return {"status": "completed"}


def analyze_repo_background(task_id: str, repo_url: str, max_bytes: int):
    """
    Analyze a repository in the background.
    
    Args:
        task_id: ID of the analysis task
        repo_url: URL of the GitHub repository
        max_bytes: Maximum file size to render
    """
    try:
        # Analyze the repository
        result = analyze_repo(repo_url, max_bytes)
        
        # Store the result in the cache
        analysis_cache[task_id] = result
    except Exception as e:
        # Store the error in the cache
        analysis_cache[task_id] = RepoAnalysisResult(
            repo_url=repo_url,
            head_commit="",
            html_content="",
            total_files=0,
            rendered_files=0,
            skipped_files=0,
            error=str(e)
        )


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the rendergit web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    uvicorn.run(app, host=host, port=port)

