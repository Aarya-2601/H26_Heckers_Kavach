"""Kavach Web Interface Runner.

Run with:
    python run_web.py
    python run_web.py --port 8080 --host 0.0.0.0
"""

import argparse
import sys
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Kavach Web Interface Runner")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable live auto-reload for dev")
    args = parser.parse_args()

    print("=" * 60)
    print(" 🛡️  KAVACH - Intelligent Dependency Auto-Healing Platform")
    print(f" 🌐 Web Dashboard running at: http://{args.host}:{args.port}")
    print(f" 📚 Tailored for target repository: https://github.com/rishrek/LinkWatch")
    print("=" * 60)

    uvicorn.run("web.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
