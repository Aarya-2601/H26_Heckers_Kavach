"""
End-to-end demo of the migration search engine on any target repository.

Demonstrates:
1. Baseline test capture on the unmodified repo.
2. Auto-heal retry loop catching the error traceback from a failed first patch.
3. A sandboxed patch (a markupsafe compatibility shim) being applied and scored.
4. Deterministic reward scoring and Mermaid DAG generation.

The simulated "Gemma" patches are built from the real first lines of the hero file,
so the diffs apply to whichever repository you point this script at.

Usage:
    python demo_engine_loop.py --hero-file pkg/report.py --repo-url https://github.com/owner/repo
    python demo_engine_loop.py --hero-file pkg/report.py --repo-path target_repo
"""

import argparse
import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.search_loop import run_migration_search

NAIVE_COMMENT = ["# Naive migration attempt\n"]
SOFT_UNICODE_SHIM = [
    "import markupsafe\n",
    "if not hasattr(markupsafe, 'soft_unicode'):\n",
    "    markupsafe.soft_unicode = str\n",
]


def make_simulated_migrator(repo_path: str, hero_file: str):
    """
    Returns a patch generator that simulates Gemma 4:
    Attempt 1: A naive attempt that fails.
    Attempt 2: An auto-healed compatibility shim resolving the markupsafe soft_unicode break.
    """
    original = (Path(repo_path) / hero_file).read_text(encoding="utf-8").splitlines(keepends=True)
    if original and not original[-1].endswith("\n"):
        original[-1] += "\n"

    def build_diff(prefix_lines):
        return "".join(
            difflib.unified_diff(
                original,
                prefix_lines + original,
                fromfile=f"a/{hero_file}",
                tofile=f"b/{hero_file}",
            )
        )

    def simulated_gemma_migrator(replacement_pkg: str, previous_error: str) -> str:
        if not previous_error:
            return build_diff(NAIVE_COMMENT)
        return build_diff(SOFT_UNICODE_SHIM)

    return simulated_gemma_migrator


def parse_args():
    parser = argparse.ArgumentParser(description="Run the migration search engine on a target repository.")
    parser.add_argument("--hero-file", required=True, help="Path of the file to migrate, relative to the repo root.")
    parser.add_argument("--repo-path", default="target_repo", help="Local repo directory (default: target_repo).")
    parser.add_argument("--repo-url", help="Git URL to clone into --repo-path if it does not exist.")
    parser.add_argument("--target-pkg", default="jinja2", help="Dependency being migrated away from.")
    parser.add_argument("--replacement-pkg", default="jinja2-modern", help="Replacement dependency.")
    parser.add_argument("--max-attempts", type=int, default=2)
    return parser.parse_args()


def main():
    args = parse_args()
    repo_path = os.path.abspath(args.repo_path)

    if not os.path.exists(repo_path):
        if not args.repo_url:
            sys.exit(f"[!] {repo_path} not found. Pass --repo-url to clone it or --repo-path to an existing repo.")
        print(f"[*] {args.repo_path} not found locally. Cloning {args.repo_url}...")
        subprocess.run(["git", "clone", args.repo_url, repo_path], check=True)

    if not (Path(repo_path) / args.hero_file).is_file():
        sys.exit(f"[!] Hero file not found: {Path(repo_path) / args.hero_file}")

    print("=" * 60)
    print(f"RUNNING PERSON 1 ENGINE ON TARGET REPOSITORY: {Path(repo_path).name}")
    print("=" * 60)

    best_node, history, mermaid = run_migration_search(
        repo_path=repo_path,
        target_pkg=args.target_pkg,
        replacement_pkg=args.replacement_pkg,
        hero_file=args.hero_file,
        patch_generator_fn=make_simulated_migrator(repo_path, args.hero_file),
        max_attempts=args.max_attempts,
    )

    print("\n--- SEARCH TREE EVALUATION SUMMARY ---")
    for node in history:
        print(f"\n[Node {node.node_id}] {node.action_name}")
        print(f"  Status: {node.status}")
        print(f"  Score:  {node.reward_score}")
        print(f"  Time:   {node.run_result.get('execution_time_ms', 0)}ms")
        print(f"  Passed: {node.run_result.get('passed')}")
        if node.reward_breakdown.get("reasons"):
            for reason in node.reward_breakdown["reasons"]:
                print(f"    * {reason}")

    print("\n--- BEST WINNING CANDIDATE ---")
    print(f"Winning Node: {best_node.node_id} ({best_node.action_name}) with Score: {best_node.reward_score}")
    print(f"Winning Patch:\n{best_node.patch_diff}")

    print("\n--- PROOF-OF-SEARCH MERMAID DAG ---")
    print(mermaid)

    # Save telemetry contract
    contract_data = {
        "winning_node": best_node.to_dict(),
        "total_nodes_explored": len(history),
        "history": [n.to_dict() for n in history],
        "mermaid_dag": mermaid,
    }
    os.makedirs("contracts", exist_ok=True)
    with open("contracts/run_result.json", "w", encoding="utf-8") as f:
        json.dump(contract_data, f, indent=2)
    print("\n[+] Updated contracts/run_result.json with full execution telemetry!")


if __name__ == "__main__":
    main()