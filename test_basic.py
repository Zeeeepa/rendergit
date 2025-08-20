#!/usr/bin/env python3
"""
Basic tests for rendergit functionality.

This script provides simple tests to verify that rendergit is working correctly.
"""

import os
import pathlib
import tempfile
import unittest

from rendergit.core import analyze_repo


class TestRendergit(unittest.TestCase):
    """Basic tests for rendergit functionality."""
    
    def test_analyze_repo(self):
        """Test that analyze_repo works with a simple repository."""
        # Use a small, public repository for testing
        repo_url = "https://github.com/Zeeeepa/rendergit"
        
        # Analyze the repository
        result = analyze_repo(repo_url)
        
        # Check that the analysis was successful
        self.assertIsNone(result.error)
        self.assertGreater(result.total_files, 0)
        self.assertGreater(result.rendered_files, 0)
        self.assertGreater(len(result.html_content), 0)
        
        # Check that the HTML content contains expected elements
        self.assertIn("<title>Flattened repo", result.html_content)
        self.assertIn("Repository:", result.html_content)
        self.assertIn("HEAD commit:", result.html_content)
        self.assertIn("Directory tree", result.html_content)
        
        # Check that both view modes are present
        self.assertIn('id="human-view"', result.html_content)
        self.assertIn('id="llm-view"', result.html_content)
    
    def test_output_file(self):
        """Test that we can write the output to a file."""
        # Use a small, public repository for testing
        repo_url = "https://github.com/Zeeeepa/rendergit"
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Analyze the repository
            result = analyze_repo(repo_url)
            
            # Write the output to the temporary file
            pathlib.Path(tmp_path).write_text(result.html_content, encoding="utf-8")
            
            # Check that the file exists and has content
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
            
            # Read the file and check its content
            content = pathlib.Path(tmp_path).read_text(encoding="utf-8")
            self.assertEqual(content, result.html_content)
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()

