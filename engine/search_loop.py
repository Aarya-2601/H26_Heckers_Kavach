"""
Inference-Time Search & Auto-Heal Engine (MCTS-style State Machine).
Orchestrates candidate generation, sandboxed test execution, reward calculation,
and produces a verifiable Proof-of-Search DAG.
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is in path for standalone execution
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from typing import Dict, Any, List, Optional, Callable, Tuple
from engine.sandbox import run_in_ephemeral_sandbox, execute_test_suite
from engine.rewards import compute_reward


class SearchNode:
    def __init__(
        self,
        node_id: str,
        parent_id: Optional[str],
        action_name: str,
        patch_diff: str = "",
        details: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.parent_id = parent_id
        self.action_name = action_name
        self.patch_diff = patch_diff
        self.details = details or {}
        self.run_result: Dict[str, Any] = {}
        self.reward_score: int = -9999
        self.reward_breakdown: Dict[str, Any] = {}
        self.status: str = "PENDING"  # PASSED, FAILED, TAMPERED, PRUNED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "action_name": self.action_name,
            "patch_diff": self.patch_diff,
            "run_result": self.run_result,
            "reward_score": self.reward_score,
            "reward_breakdown": self.reward_breakdown,
            "status": self.status
        }


def generate_mermaid_dag(nodes: List[SearchNode]) -> str:
    """
    Renders the search path as an interactive Mermaid diagram for CAPSULE.md.
    """
    lines = ["graph TD"]
    for node in nodes:
        # Style node based on status
        if node.status == "PASSED":
            style = f'class {node.node_id} passed;'
            label = f'{node.node_id}["{node.action_name}<br/>Score: {node.reward_score} (PASSED)"]'
        elif node.status == "TAMPERED":
            label = f'{node.node_id}["{node.action_name}<br/>Score: {node.reward_score} (TAMPERED)"]'
        elif node.node_id == "node_0":
            label = f'{node.node_id}["{node.action_name}<br/>(Baseline)"]'
        else:
            label = f'{node.node_id}["{node.action_name}<br/>Score: {node.reward_score} (FAILED)"]'
        
        lines.append(f"    {label}")
        if node.parent_id:
            lines.append(f"    {node.parent_id} --> {node.node_id}")

    lines.append("    classDef passed fill:#2ea44f,stroke:#22863a,color:#fff;")
    lines.append("    classDef failed fill:#cb2431,stroke:#b31d28,color:#fff;")
    return "\n".join(lines)


def run_migration_search(
    repo_path: str,
    target_pkg: str,
    replacement_pkg: str,
    hero_file: str,
    patch_generator_fn: Optional[Callable[[str, Optional[str]], str]] = None,
    test_cmd: Optional[List[str]] = None,
    max_attempts: int = 3
) -> Tuple[SearchNode, List[SearchNode], str]:
    """
    Executes iterative MCTS search loop over AST migration proposals:
    1. Evaluates Node 0 (Baseline).
    2. Generates initial migration proposal (Node 1).
    3. If tests fail, feeds stderr back to generator to spawn Auto-Heal retries (Node 2, Node 3).
    4. Backtracks and selects highest reward node.
    """
    history: List[SearchNode] = []
    seen_error_signatures = set()

    # --- Node 0: Establish Baseline ---
    baseline_result = execute_test_suite(repo_path, test_cmd=test_cmd)
    baseline_time_ms = baseline_result.get("execution_time_ms", 150)
    
    root_node = SearchNode(
        node_id="node_0",
        parent_id=None,
        action_name=f"Baseline ({target_pkg})",
        patch_diff="",
        details={"baseline_time_ms": baseline_time_ms}
    )
    root_node.run_result = baseline_result
    root_node.reward_score = 0
    root_node.status = "BASELINE"
    history.append(root_node)

    current_parent_id = "node_0"
    last_stderr = ""
    best_node = root_node

    for attempt in range(1, max_attempts + 1):
        node_id = f"node_{attempt}"
        action_name = f"Attempt {attempt}: Direct Refactor" if attempt == 1 else f"Attempt {attempt}: Auto-Heal (Shim/Fix)"

        # Generate patch using provided generator function or fallback mock generator
        if patch_generator_fn:
            patch = patch_generator_fn(replacement_pkg, last_stderr)
        else:
            # Standalone fallback mock generator
            if attempt == 1:
                # Mock attempt 1: Fails with a missing module or method error
                patch = f"--- a/{hero_file}\n+++ b/{hero_file}\n@@ -1,3 +1,3 @@\n-import {target_pkg}\n+import {replacement_pkg}\n"
            else:
                # Mock attempt 2: Fixed / pass
                patch = f"--- a/{hero_file}\n+++ b/{hero_file}\n@@ -1,4 +1,4 @@\n-import {target_pkg}\n+import {replacement_pkg}\n+# Auto-heal shim applied\n"

        node = SearchNode(
            node_id=node_id,
            parent_id=current_parent_id,
            action_name=action_name,
            patch_diff=patch
        )

        # Execute in ephemeral sandbox
        run_res = run_in_ephemeral_sandbox(repo_path, patch_diff=patch, test_cmd=test_cmd)
        node.run_result = run_res

        # Calculate reward score
        score, breakdown = compute_reward(
            run_res,
            patch_diff=patch,
            baseline_time_ms=baseline_time_ms,
            seen_error_signatures=seen_error_signatures
        )
        node.reward_score = score
        node.reward_breakdown = breakdown

        if breakdown.get("tampering_detected"):
            node.status = "TAMPERED"
        elif run_res.get("passed", False):
            node.status = "PASSED"
        else:
            node.status = "FAILED"

        history.append(node)

        # Update best candidate
        if node.reward_score > best_node.reward_score and node.status != "TAMPERED":
            best_node = node

        # If tests passed cleanly, stop searching early
        if node.status == "PASSED":
            break

        # Otherwise, feed back stderr to next attempt
        last_stderr = run_res.get("raw_stderr", "")
        current_parent_id = node_id

    mermaid_chart = generate_mermaid_dag(history)
    return best_node, history, mermaid_chart


if __name__ == "__main__":
    print("[Person 1] Self-Testing engine/search_loop.py...")

    # Create a small dummy repo folder to simulate real execution
    import tempfile
    with tempfile.TemporaryDirectory() as temp_repo:
        dummy_code = os.path.join(temp_repo, "app.py")
        dummy_test = os.path.join(temp_repo, "test_app.py")

        with open(dummy_code, "w") as f:
            f.write("def get_data():\n    return 'legacy_ok'\n")

        with open(dummy_test, "w") as f:
            f.write("import app\ndef test_ok():\n    assert app.get_data() != ''\n")

        # Mock generator simulating an initial syntax break, then an auto-heal fix
        def mock_ai_generator(replacement: str, previous_error: Optional[str]) -> str:
            if not previous_error:
                # First attempt: intentional syntax error to trigger auto-heal
                return "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def get_data():\n-    return 'legacy_ok'\n+    return legacy_broken(\n"
            else:
                # Second attempt: auto-healed fix
                return "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def get_data():\n-    return 'legacy_ok'\n+    return 'migrated_httpx_ok'\n"

        best_node, history, mermaid = run_migration_search(
            repo_path=temp_repo,
            target_pkg="requests",
            replacement_pkg="httpx",
            hero_file="app.py",
            patch_generator_fn=mock_ai_generator,
            test_cmd=["pytest"]
        )

        print(f"\nSearch Finished in {len(history)} nodes.")
        print(f"Best Node: {best_node.node_id} ({best_node.action_name}) - Score: {best_node.reward_score}")
        print("\nGenerated Mermaid DAG:\n")
        print(mermaid)

        assert best_node.status == "PASSED", f"Expected winning node to have passed, got {best_node.status}"
        print("\nAll search_loop.py self-tests PASSED successfully!")
