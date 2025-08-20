#!/usr/bin/env python3
"""
Command-line interface for rendergit.

This module provides the CLI functionality for rendergit, allowing users
to render GitHub repositories from the command line.
"""

import argparse
import pathlib
import sys
import webbrowser

from rendergit.core import analyze_repo, MAX_DEFAULT_BYTES, derive_temp_output_path


def main() -> int:
    """Main CLI entry point."""
    ap = argparse.ArgumentParser(description="Flatten a GitHub repo to a single HTML page")
    ap.add_argument("repo_url", help="GitHub repo URL (https://github.com/owner/repo[.git])")
    ap.add_argument("-o", "--out", help="Output HTML file path (default: temporary file derived from repo name)")
    ap.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES, 
                   help="Max file size to render (bytes); larger files are listed but skipped")
    ap.add_argument("--no-open", action="store_true", help="Don't open the HTML file in browser after generation")
    ap.add_argument("--server", action="store_true", help="Start web server instead of generating a file")
    ap.add_argument("--port", type=int, default=8000, help="Port for web server (default: 8000)")
    args = ap.parse_args()
    
    # If server mode is requested, start the web server
    if args.server:
        try:
            from rendergit.server import start_server
            print(f"🌐 Starting rendergit web server on port {args.port}...", file=sys.stderr)
            start_server(port=args.port)
            return 0
        except ImportError:
            print("Error: Web server dependencies not installed. Install with `pip install rendergit[server]`.", 
                  file=sys.stderr)
            return 1
    
    # Set default output path if not provided
    if args.out is None:
        args.out = str(derive_temp_output_path(args.repo_url))
    
    print(f"📁 Analyzing {args.repo_url}...", file=sys.stderr)
    result = analyze_repo(args.repo_url, args.max_bytes)
    
    if result.error:
        print(f"❌ Error: {result.error}", file=sys.stderr)
        return 1
    
    print(f"✓ Found {result.total_files} files total "
          f"({result.rendered_files} rendered, {result.skipped_files} skipped)", file=sys.stderr)
    
    out_path = pathlib.Path(args.out)
    print(f"💾 Writing HTML file: {out_path.resolve()}", file=sys.stderr)
    out_path.write_text(result.html_content, encoding="utf-8")
    file_size = out_path.stat().st_size
    print(f"✓ Wrote {file_size} bytes to {out_path}", file=sys.stderr)
    
    if not args.no_open:
        print(f"🌐 Opening {out_path} in browser...", file=sys.stderr)
        webbrowser.open(f"file://{out_path.resolve()}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

