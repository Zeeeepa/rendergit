#!/usr/bin/env python3
"""
Rendergit Server - Web UI for flattening GitHub repositories.

This module provides a Flask-based web server that allows users to:
1. Enter a GitHub repository URL
2. View a quick structure summary (directory tree, file counts)
3. Generate and view the full flattened HTML

Designed to work well in WSL2 environments where the standard rendergit
command might fail due to lack of GUI browser access.

Usage:
    rendergit-serve [--host HOST] [--port PORT]
"""

import argparse
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from flask import Flask, render_template, request, Response, jsonify, abort

# Import from the main module
from repo_to_single_page import (
    git_clone, git_head_commit, collect_files, try_tree_command,
    build_html, MAX_DEFAULT_BYTES, FileInfo
)

app = Flask(__name__)

# GitHub URL validation regex
GITHUB_URL_PATTERN = re.compile(
    r'^https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(?:\.git)?/?$'
)

def validate_github_url(url: str) -> bool:
    """Validate that the URL is a GitHub repository URL."""
    return bool(GITHUB_URL_PATTERN.match(url))

def extract_repo_name(url: str) -> str:
    """Extract repository name from GitHub URL."""
    parts = url.rstrip('/').split('/')
    repo_name = parts[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name

def build_structure_summary(repo_url: str, repo_dir: Path, max_bytes: int = MAX_DEFAULT_BYTES) -> Dict[str, Any]:
    """
    Build a structure-only summary of the repository.
    
    Returns a dict with:
    - repo_url: Original URL
    - head_commit: HEAD commit hash
    - tree_text: Directory tree text
    - stats: File statistics
    """
    head_commit = git_head_commit(str(repo_dir))
    infos = collect_files(repo_dir, max_bytes)
    
    # Generate tree text
    tree_text = try_tree_command(repo_dir)
    
    # Calculate stats
    rendered = [i for i in infos if i.decision.include]
    skipped_binary = [i for i in infos if i.decision.reason == "binary"]
    skipped_large = [i for i in infos if i.decision.reason == "too_large"]
    skipped_ignored = [i for i in infos if i.decision.reason == "ignored"]
    total_files = len(rendered) + len(skipped_binary) + len(skipped_large) + len(skipped_ignored)
    
    # Build stats dict
    stats = {
        "total_files": total_files,
        "rendered_count": len(rendered),
        "skipped_binary_count": len(skipped_binary),
        "skipped_large_count": len(skipped_large),
        "skipped_ignored_count": len(skipped_ignored),
    }
    
    return {
        "repo_url": repo_url,
        "head_commit": head_commit,
        "tree_text": tree_text,
        "stats": stats,
    }

@app.route('/')
def index():
    """Render the main page with the repository URL form."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze a GitHub repository and return either:
    - Structure summary (quick)
    - Full flattened HTML (slower, larger)
    """
    repo_url = request.form.get('repo_url', '').strip()
    mode = request.form.get('mode', 'structure')  # 'structure' or 'full'
    
    # Validate URL
    if not repo_url:
        return jsonify({"error": "Repository URL is required"}), 400
    
    if not validate_github_url(repo_url):
        return jsonify({"error": "Invalid GitHub repository URL"}), 400
    
    # Create temporary directory
    with tempfile.TemporaryDirectory(prefix="rendergit_") as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        
        try:
            # Clone the repository
            git_clone(repo_url, str(repo_dir))
            
            if mode == 'structure':
                # Return structure summary
                summary = build_structure_summary(repo_url, repo_dir)
                return jsonify(summary)
            else:
                # Generate full HTML
                head_commit = git_head_commit(str(repo_dir))
                infos = collect_files(repo_dir, MAX_DEFAULT_BYTES)
                html_content = build_html(repo_url, repo_dir, head_commit, infos)
                
                # Return as HTML response
                return Response(html_content, mimetype='text/html')
                
        except Exception as e:
            app.logger.error(f"Error processing repository: {str(e)}")
            return jsonify({"error": f"Failed to process repository: {str(e)}"}), 500

def cli():
    """Command-line entry point for the server."""
    parser = argparse.ArgumentParser(description="Run the rendergit web server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Print startup message
    print(f"Starting rendergit server at http://{args.host}:{args.port}")
    if args.host == '0.0.0.0':
        print(f"Access from Windows via http://localhost:{args.port}")
    
    # Run the Flask app
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    cli()

