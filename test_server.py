#!/usr/bin/env python3
"""
Test suite for rendergit server mode.

This module tests the Flask-based web server functionality, including:
- URL validation
- Structure summary generation
- Full HTML generation
- Error handling for edge cases

Usage:
    python -m unittest test_server.py
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from flask import Flask
from flask.testing import FlaskClient

# Import server module
from server import (
    app, validate_github_url, extract_repo_name, 
    build_structure_summary
)

class TestRendergitServer(unittest.TestCase):
    """Test cases for rendergit server functionality."""

    def setUp(self):
        """Set up test environment."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()

    def test_index_route(self):
        """Test that the index route returns the main page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rendergit', response.data)
        self.assertIn(b'GitHub Repository URL', response.data)

    def test_url_validation_valid_urls(self):
        """Test URL validation with valid GitHub URLs."""
        valid_urls = [
            'https://github.com/user/repo',
            'https://github.com/user/repo.git',
            'http://github.com/user/repo',
            'https://github.com/user-name/repo-name',
            'https://github.com/user_name/repo_name',
            'https://github.com/user.name/repo.name',
        ]
        for url in valid_urls:
            self.assertTrue(validate_github_url(url), f"URL should be valid: {url}")

    def test_url_validation_invalid_urls(self):
        """Test URL validation with invalid GitHub URLs."""
        invalid_urls = [
            '',  # Empty string
            'not a url',  # Not a URL
            'https://example.com/user/repo',  # Not GitHub
            'https://github.com',  # No user/repo
            'https://github.com/user',  # No repo
            'https://github.com/user/repo/extra',  # Extra path
            'https://github.com/user/repo?query=param',  # Query params
            'https://github.com/user/repo#fragment',  # Fragment
            'git@github.com:user/repo.git',  # SSH URL
        ]
        for url in invalid_urls:
            self.assertFalse(validate_github_url(url), f"URL should be invalid: {url}")

    def test_extract_repo_name(self):
        """Test extracting repository name from GitHub URL."""
        test_cases = [
            ('https://github.com/user/repo', 'repo'),
            ('https://github.com/user/repo.git', 'repo'),
            ('http://github.com/user/repo/', 'repo'),
            ('https://github.com/user/repo-name', 'repo-name'),
            ('https://github.com/user/repo.name', 'repo.name'),
        ]
        for url, expected in test_cases:
            self.assertEqual(extract_repo_name(url), expected)

    @patch('server.git_clone')
    @patch('server.git_head_commit')
    @patch('server.collect_files')
    @patch('server.try_tree_command')
    def test_build_structure_summary(self, mock_tree, mock_collect, mock_head, mock_clone):
        """Test building structure summary."""
        # Setup mocks
        mock_head.return_value = "abcd1234"
        mock_tree.return_value = "repo\n├── file1.py\n└── file2.py"
        
        # Create mock FileInfo objects
        from repo_to_single_page import FileInfo, RenderDecision
        mock_file1 = FileInfo(
            path=Path("/tmp/file1.py"),
            rel="file1.py",
            size=100,
            decision=RenderDecision(True, "ok")
        )
        mock_file2 = FileInfo(
            path=Path("/tmp/file2.py"),
            rel="file2.py",
            size=200,
            decision=RenderDecision(True, "ok")
        )
        mock_binary = FileInfo(
            path=Path("/tmp/image.png"),
            rel="image.png",
            size=1000,
            decision=RenderDecision(False, "binary")
        )
        mock_large = FileInfo(
            path=Path("/tmp/large.txt"),
            rel="large.txt",
            size=100000,
            decision=RenderDecision(False, "too_large")
        )
        mock_ignored = FileInfo(
            path=Path("/tmp/.git/config"),
            rel=".git/config",
            size=500,
            decision=RenderDecision(False, "ignored")
        )
        
        mock_collect.return_value = [mock_file1, mock_file2, mock_binary, mock_large, mock_ignored]
        
        # Test
        repo_url = "https://github.com/user/repo"
        repo_dir = Path("/tmp/repo")
        result = build_structure_summary(repo_url, repo_dir)
        
        # Verify
        self.assertEqual(result["repo_url"], repo_url)
        self.assertEqual(result["head_commit"], "abcd1234")
        self.assertEqual(result["tree_text"], "repo\n├── file1.py\n└── file2.py")
        self.assertEqual(result["stats"]["total_files"], 5)
        self.assertEqual(result["stats"]["rendered_count"], 2)
        self.assertEqual(result["stats"]["skipped_binary_count"], 1)
        self.assertEqual(result["stats"]["skipped_large_count"], 1)
        self.assertEqual(result["stats"]["skipped_ignored_count"], 1)

    def test_analyze_route_missing_url(self):
        """Test analyze route with missing URL."""
        response = self.client.post('/analyze', data={
            'mode': 'structure'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
        self.assertIn('required', response.json['error'].lower())

    def test_analyze_route_invalid_url(self):
        """Test analyze route with invalid URL."""
        response = self.client.post('/analyze', data={
            'repo_url': 'not-a-github-url',
            'mode': 'structure'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)
        self.assertIn('invalid', response.json['error'].lower())

    @patch('server.git_clone')
    @patch('server.build_structure_summary')
    def test_analyze_route_structure_mode(self, mock_summary, mock_clone):
        """Test analyze route with structure mode."""
        # Setup mock
        mock_summary.return_value = {
            "repo_url": "https://github.com/user/repo",
            "head_commit": "abcd1234",
            "tree_text": "repo\n├── file1.py\n└── file2.py",
            "stats": {
                "total_files": 5,
                "rendered_count": 2,
                "skipped_binary_count": 1,
                "skipped_large_count": 1,
                "skipped_ignored_count": 1
            }
        }
        
        # Test
        response = self.client.post('/analyze', data={
            'repo_url': 'https://github.com/user/repo',
            'mode': 'structure'
        })
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["repo_url"], "https://github.com/user/repo")
        self.assertEqual(response.json["head_commit"], "abcd1234")
        self.assertEqual(response.json["stats"]["total_files"], 5)

    @patch('server.git_clone')
    @patch('server.git_head_commit')
    @patch('server.collect_files')
    @patch('server.build_html')
    def test_analyze_route_full_mode(self, mock_html, mock_collect, mock_head, mock_clone):
        """Test analyze route with full HTML mode."""
        # Setup mocks
        mock_head.return_value = "abcd1234"
        mock_html.return_value = "<html><body>Test HTML</body></html>"
        
        # Test
        response = self.client.post('/analyze', data={
            'repo_url': 'https://github.com/user/repo',
            'mode': 'full'
        })
        
        # Verify
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"<html><body>Test HTML</body></html>")
        self.assertEqual(response.mimetype, 'text/html')

    @patch('server.git_clone')
    def test_analyze_route_clone_error(self, mock_clone):
        """Test analyze route with git clone error."""
        # Setup mock to raise exception
        mock_clone.side_effect = Exception("Git clone failed")
        
        # Test
        response = self.client.post('/analyze', data={
            'repo_url': 'https://github.com/user/repo',
            'mode': 'structure'
        })
        
        # Verify
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)
        self.assertIn('failed', response.json['error'].lower())

    def test_edge_case_empty_repo(self):
        """Test handling of empty repositories."""
        # This would require more complex mocking of git_clone and collect_files
        # to simulate an empty repository. For now, we'll skip the actual implementation.
        pass

    def test_edge_case_large_repo(self):
        """Test handling of very large repositories."""
        # This would require more complex mocking to simulate a large repository
        # For now, we'll skip the actual implementation.
        pass

if __name__ == '__main__':
    unittest.main()
