"""Kavach Web Interface Runner.

Run with:
    python run_web.py
    python run_web.py --port 8080 --host 0.0.0.0
"""

import argparse
import sys
from pathlib import Path

# Ensure root directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Soft_unicode shim for markup/jinja compatibility
import markupsafe
if not hasattr(markupsafe, "soft_unicode"):
    markupsafe.soft_unicode = str

from web.server import app


def main():
    parser = argparse.ArgumentParser(description="Kavach Web Interface Runner")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print("=" * 60)
    print(" 🛡️  KAVACH - Intelligent Dependency Auto-Healing Platform")
    print(f" 🌐 Web Dashboard running at: http://{args.host}:{args.port}")
    print(" 📚 Select any public GitHub repository from the dashboard to analyze")
    print("=" * 60)

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()