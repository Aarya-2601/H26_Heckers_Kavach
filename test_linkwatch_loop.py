"""
End-to-End Test of Person 1 Engine against the Organizer Target Repo: LinkWatch.
Demonstrates:
1. Baseline test capture (1 failing test in LinkWatch: Jinja2/markupsafe incompatibility).
2. Auto-heal retry loop catching the error traceback.
3. Successful sandboxed patch application passing 10/10 tests.
4. Deterministic reward scoring and Mermaid DAG generation.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.search_loop import run_migration_search
from engine.rewards import compute_reward


def simulated_gemma_linkwatch_migrator(replacement_pkg: str, previous_error: str) -> str:
    """
    Simulates Gemma 4 generating:
    Attempt 1: A naive attempt that fails.
    Attempt 2: An auto-healed compatibility shim resolving the markupsafe soft_unicode break.
    """
    if not previous_error:
        # Attempt 1: Naive patch that still leaves the import broken
        return (
            "--- a/linkwatch/report.py\n"
            "+++ b/linkwatch/report.py\n"
            "@@ -1,3 +1,4 @@\n"
            "+# Naive migration attempt\n"
            " from datetime import datetime\n"
        )
    else:
        # Attempt 2: Auto-heal shim patch that fixes the soft_unicode incompatibility
        return (
            "--- a/linkwatch/report.py\n"
            "+++ b/linkwatch/report.py\n"
            "@@ -1,4 +1,7 @@\n"
            "+import markupsafe\n"
            "+if not hasattr(markupsafe, 'soft_unicode'):\n"
            "+    markupsafe.soft_unicode = str\n"
            " from datetime import datetime\n"
            " \n"
            " from jinja2 import Environment, FileSystemLoader, select_autoescape\n"
        )


def main():
    repo_path = os.path.abspath("target_repo")
    if not os.path.exists(repo_path):
        import subprocess
        print("[*] target_repo not found locally. Cloning LinkWatch...")
        subprocess.run(["git", "clone", "https://github.com/rishrek/LinkWatch", repo_path], check=True)

    print("=" * 60)
    print("RUNNING PERSON 1 ENGINE ON REAL LINKWATCH TARGET REPOSITORY")
    print("=" * 60)

    best_node, history, mermaid = run_migration_search(
        repo_path=repo_path,
        target_pkg="jinja2",
        replacement_pkg="jinja2-modern",
        hero_file="linkwatch/report.py",
        patch_generator_fn=simulated_gemma_linkwatch_migrator,
        max_attempts=2
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
        "mermaid_dag": mermaid
    }
    with open("contracts/run_result.json", "w", encoding="utf-8") as f:
        import json
        json.dump(contract_data, f, indent=2)
    print("\n[+] Updated contracts/run_result.json with full execution telemetry!")


if __name__ == "__main__":
    main()
