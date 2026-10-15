"""
Engine package for Dependency Resilience Lab.
Includes sandboxed execution, deterministic reward calculation, and MCTS search loop.
"""

from engine.sandbox import execute_test_suite, run_in_ephemeral_sandbox
from engine.rewards import compute_reward
from engine.search_loop import run_migration_search, SearchNode, generate_mermaid_dag

__all__ = [
    "execute_test_suite",
    "run_in_ephemeral_sandbox",
    "compute_reward",
    "run_migration_search",
    "SearchNode",
    "generate_mermaid_dag"
]
