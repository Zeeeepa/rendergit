#!/usr/bin/env python3
"""
Test script for rendergit server with real repositories.

This script tests the rendergit server with real GitHub repositories,
validating that it can handle various edge cases and real-world scenarios.

Usage:
    python test_real_repos.py
"""

import argparse
import json
import requests
import sys
import time
from pathlib import Path

# Test repositories with different characteristics
TEST_REPOS = [
    {
        "url": "https://github.com/karpathy/nanoGPT",
        "description": "Small but complete GPT implementation",
        "characteristics": ["Python", "Medium size", "Popular"]
    },
    {
        "url": "https://github.com/karpathy/micrograd",
        "description": "Tiny autograd engine",
        "characteristics": ["Python", "Small size", "Educational"]
    },
    {
        "url": "https://github.com/Zeeeepa/rendergit",
        "description": "The rendergit repo itself (self-test)",
        "characteristics": ["Python", "Small size", "Meta"]
    },
    {
        "url": "https://github.com/microsoft/vscode",
        "description": "VS Code (large repo)",
        "characteristics": ["TypeScript", "Very large", "Complex structure"]
    },
    {
        "url": "https://github.com/pallets/flask",
        "description": "Flask web framework",
        "characteristics": ["Python", "Medium size", "Web framework"]
    },
]

# Edge cases and false positives to test
EDGE_CASES = [
    {
        "url": "https://github.com/empty/repo",  # This doesn't exist, should be handled gracefully
        "description": "Non-existent repository",
        "expected_error": True
    },
    {
        "url": "https://github.com",  # Invalid URL format
        "description": "Invalid GitHub URL (no user/repo)",
        "expected_error": True
    },
    {
        "url": "not a url",  # Not a URL at all
        "description": "Not a URL at all",
        "expected_error": True
    },
    {
        "url": "https://example.com/user/repo",  # Not GitHub
        "description": "Non-GitHub URL",
        "expected_error": True
    },
]

def test_structure_mode(server_url, repo_url):
    """Test structure-only mode for a repository."""
    print(f"Testing structure mode for {repo_url}...")
    
    try:
        response = requests.post(
            f"{server_url}/analyze",
            data={"repo_url": repo_url, "mode": "structure"},
            timeout=60  # Longer timeout for larger repos
        )
        
        if response.status_code != 200:
            print(f"  ❌ Error: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_keys = ["repo_url", "head_commit", "tree_text", "stats"]
        for key in required_keys:
            if key not in data:
                print(f"  ❌ Missing key in response: {key}")
                return False
        
        # Validate stats
        stats_keys = ["total_files", "rendered_count", "skipped_binary_count", 
                     "skipped_large_count", "skipped_ignored_count"]
        for key in stats_keys:
            if key not in data["stats"]:
                print(f"  ❌ Missing key in stats: {key}")
                return False
        
        # Print summary
        print(f"  ✅ Success: {data['stats']['total_files']} files, {data['stats']['rendered_count']} rendered")
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return False

def test_full_mode(server_url, repo_url):
    """Test full HTML mode for a repository."""
    print(f"Testing full HTML mode for {repo_url}...")
    
    try:
        response = requests.post(
            f"{server_url}/analyze",
            data={"repo_url": repo_url, "mode": "full"},
            timeout=120  # Even longer timeout for full HTML generation
        )
        
        if response.status_code != 200:
            print(f"  ❌ Error: {response.status_code} - {response.text}")
            return False
        
        # Check that response is HTML
        if "text/html" not in response.headers.get("Content-Type", ""):
            print(f"  ❌ Response is not HTML: {response.headers.get('Content-Type')}")
            return False
        
        # Check for key HTML elements
        html = response.text
        if "<html" not in html or "<body" not in html:
            print(f"  ❌ Response doesn't look like HTML")
            return False
        
        # Check for expected content
        expected_elements = ["<title>", "Flattened repo", "Directory tree", "Table of contents"]
        for element in expected_elements:
            if element not in html:
                print(f"  ❌ Missing expected element: {element}")
                return False
        
        # Print summary
        html_size = len(html) / 1024  # KB
        print(f"  ✅ Success: {html_size:.1f} KB of HTML generated")
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return False

def test_edge_case(server_url, edge_case):
    """Test an edge case."""
    url = edge_case["url"]
    description = edge_case["description"]
    expected_error = edge_case["expected_error"]
    
    print(f"Testing edge case: {description} ({url})...")
    
    try:
        response = requests.post(
            f"{server_url}/analyze",
            data={"repo_url": url, "mode": "structure"},
            timeout=30
        )
        
        if expected_error:
            if response.status_code >= 400:
                print(f"  ✅ Expected error received: {response.status_code}")
                return True
            else:
                print(f"  ❌ Expected error, but got success: {response.status_code}")
                return False
        else:
            if response.status_code == 200:
                print(f"  ✅ Success as expected")
                return True
            else:
                print(f"  ❌ Expected success, but got error: {response.status_code}")
                return False
                
    except Exception as e:
        if expected_error:
            print(f"  ✅ Expected error (exception): {str(e)}")
            return True
        else:
            print(f"  ❌ Unexpected exception: {str(e)}")
            return False

def main():
    """Run the tests."""
    parser = argparse.ArgumentParser(description="Test rendergit server with real repositories")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL (default: http://localhost:8000)")
    parser.add_argument("--skip-full", action="store_true", help="Skip full HTML tests (faster)")
    parser.add_argument("--only-edge-cases", action="store_true", help="Only test edge cases")
    args = parser.parse_args()
    
    server_url = args.server
    
    # Check if server is running
    try:
        response = requests.get(server_url)
        if response.status_code != 200:
            print(f"Server at {server_url} returned status code {response.status_code}")
            return 1
    except Exception as e:
        print(f"Error connecting to server at {server_url}: {str(e)}")
        print("Make sure the server is running with: rendergit-serve --host 0.0.0.0 --port 8000")
        return 1
    
    print(f"Testing rendergit server at {server_url}")
    
    results = {
        "structure_mode": [],
        "full_mode": [],
        "edge_cases": []
    }
    
    # Test real repositories
    if not args.only_edge_cases:
        for repo in TEST_REPOS:
            url = repo["url"]
            
            # Test structure mode
            structure_result = test_structure_mode(server_url, url)
            results["structure_mode"].append({
                "url": url,
                "success": structure_result
            })
            
            # Test full mode (unless skipped)
            if not args.skip_full:
                full_result = test_full_mode(server_url, url)
                results["full_mode"].append({
                    "url": url,
                    "success": full_result
                })
            
            print()  # Blank line between repos
    
    # Test edge cases
    for edge_case in EDGE_CASES:
        edge_result = test_edge_case(server_url, edge_case)
        results["edge_cases"].append({
            "description": edge_case["description"],
            "url": edge_case["url"],
            "success": edge_result
        })
        print()  # Blank line between edge cases
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    
    if not args.only_edge_cases:
        structure_success = sum(1 for r in results["structure_mode"] if r["success"])
        print(f"Structure mode: {structure_success}/{len(results['structure_mode'])} successful")
        
        if not args.skip_full:
            full_success = sum(1 for r in results["full_mode"] if r["success"])
            print(f"Full HTML mode: {full_success}/{len(results['full_mode'])} successful")
    
    edge_success = sum(1 for r in results["edge_cases"] if r["success"])
    print(f"Edge cases: {edge_success}/{len(results['edge_cases'])} successful")
    
    # Determine overall success
    all_tests = (
        results["structure_mode"] + 
        results["full_mode"] + 
        results["edge_cases"]
    )
    total_success = sum(1 for r in all_tests if r["success"])
    total_tests = len(all_tests)
    
    print(f"\nOverall: {total_success}/{total_tests} tests passed ({total_success/total_tests*100:.1f}%)")
    
    return 0 if total_success == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
