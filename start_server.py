#!/usr/bin/env python3
"""
Startup script for rendergit web server.

This script provides a simple way to start the rendergit web server.
"""

import argparse
import sys

def main():
    """Parse arguments and start the server."""
    parser = argparse.ArgumentParser(description="Start the rendergit web server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    args = parser.parse_args()
    
    try:
        from rendergit.server import start_server
        print(f"🚀 Starting rendergit web server on {args.host}:{args.port}")
        print(f"📊 Open http://localhost:{args.port} in your browser")
        start_server(host=args.host, port=args.port)
        return 0
    except ImportError:
        print("Error: rendergit server dependencies not installed.", file=sys.stderr)
        print("Install with: pip install rendergit[server]", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

