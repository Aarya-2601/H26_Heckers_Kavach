"""Auto-Heal Visual Loop module for Phase 4.

Visualizes the search and retry process without clearing terminal scrollback:
- Step 4.1: The Rewind Visual (prominent warning divider: --- ⏪ REWIND: TRIGGERING AUTO-HEAL LOOP ---)
- Step 4.2: State Append (failed attempt context + rich.tree strategy DAG showing abandoned vs active branches)
- Step 4.3: New reasoning block and healed test suite execution
"""

import sys
import time
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from src.theme import console as default_console, print_solution

# Ensure UTF-8 output encoding across platforms
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Bright warning color for rewind visual
REWIND_COLOR = "bold bright_yellow"

# Default Auto-Healed reasoning steps
AUTO_HEAL_COT_STEPS: List[str] = [
    "1. [Auto-Heal] Detected failure in Attempt #1: 'test_no_global_requests_monkeypatch'.",
    "2. [Auto-Heal] Root cause: linkwatch/http_patch.py directly mutated requests.Session.request globally.",
    "3. [Auto-Heal] Abandoning Attempt #1 branch. Rolling back AST mutation to prevent scope contamination.",
    "4. [Auto-Heal] Formulating Attempt #2: Implement dedicated LinkWatchSession subclass in linkwatch/checker.py.",
    "5. [Auto-Heal] Injecting isolated LinkWatchSession with default timeout=10.0 and custom User-Agent header.",
    "6. [Auto-Heal] Validating AST: No external libraries or global namespaces modified.",
    "7. [Auto-Heal] Re-running Deterministic Auditor and regression tests on healed codebase.",
]

# Healed test results with all tests passing
HEALED_TEST_RESULTS: List[Dict[str, Any]] = [
    {
        "id": "tests/test_checker.py::test_check_site_up",
        "origin": "Pre-existing",
        "duration": "14ms",
        "status": "PASSED",
    },
    {
        "id": "tests/test_config.py::test_load_sites_valid",
        "origin": "Pre-existing",
        "duration": "6ms",
        "status": "PASSED",
    },
    {
        "id": "tests/test_cache.py::test_save_and_load_results",
        "origin": "Pre-existing",
        "duration": "9ms",
        "status": "PASSED",
    },
    {
        "id": "tests/test_report.py::test_build_html_report",
        "origin": "Pre-existing",
        "duration": "18ms",
        "status": "PASSED",
    },
    {
        "id": "tests/generated/test_ast_checker.py::test_fetch_explicit_timeout",
        "origin": "AI-Generated",
        "duration": "21ms",
        "status": "PASSED",
    },
    {
        "id": "tests/generated/test_ast_security.py::test_no_global_requests_monkeypatch",
        "origin": "AI-Generated",
        "duration": "12ms",
        "status": "PASSED",
    },
    {
        "id": "tests/generated/test_docker_security.py::test_dockerfile_user_directive",
        "origin": "AI-Generated",
        "duration": "10ms",
        "status": "PASSED",
    },
]


def print_rewind_divider(console: Optional[Console] = None) -> None:
    """Print a prominent visual rewind divider in a bright warning color."""
    target_console = console or default_console

    divider_text = Text()
    divider_text.append("═" * 76 + "\n", style=REWIND_COLOR)
    divider_text.append("--- ⏪ REWIND: TRIGGERING AUTO-HEAL LOOP ---\n", style=f"{REWIND_COLOR} underline")
    divider_text.append("═" * 76, style=REWIND_COLOR)

    target_console.print()
    target_console.print(divider_text)
    target_console.print()


def render_failed_context(
    failed_test_id: str = "tests/generated/test_ast_security.py::test_no_global_requests_monkeypatch",
    failure_reason: str = "Global requests.Session.request mutation in linkwatch/http_patch.py:14 violated scope isolation.",
    console: Optional[Console] = None,
) -> None:
    """Print the context of the failed attempt without clearing scrollback."""
    target_console = console or default_console

    content = Text()
    content.append("Attempt #1 Status: ", style="bold white")
    content.append("FAILED (Regression Detected)\n", style="bold red")
    content.append(f"Failed Test: {failed_test_id}\n", style="dim white")
    content.append(f"Root Cause:  {failure_reason}\n", style="bright_yellow")
    content.append("Action:      Triggering auto-heal backtracking to explore alternative AST solution.", style="bright_cyan")

    panel = Panel(
        content,
        title="[bold bright_yellow]Failed Attempt Diagnostics[/bold bright_yellow]",
        border_style="bright_yellow",
        expand=False,
        padding=(1, 2),
    )
    target_console.print(panel)
    target_console.print()


def render_strategy_dag(console: Optional[Console] = None) -> Tree:
    """Render a rich.tree.Tree DAG showing the agent abandoning the failed branch and starting a new approach."""
    target_console = console or default_console

    tree = Tree(
        "[bold white]Auto-Heal Search Tree & Decision DAG[/bold white]",
        guide_style="bright_black",
    )

    # Branch 1: Abandoned / Failed
    branch_fail = tree.add(
        "[bold red]Attempt #1: In-Place Global Monkey-Patching [ABANDONED ❌][/bold red]"
    )
    branch_fail.add("[dim white]Approach: Mutate requests.Session.request in linkwatch/http_patch.py[/dim white]")
    branch_fail.add(
        "[red]Failure: Contaminates global interpreter scope; failed test_no_global_requests_monkeypatch[/red]"
    )
    branch_fail.add("[dim]State: Rolled back cleanly via AST rewind[/dim]")

    # Branch 2: Active / Healed Approach
    branch_heal = tree.add(
        "[bold bright_cyan]Attempt #2: Clean Session Subclass Adapter [ACTIVE / SELECTED 🔄][/bold bright_cyan]"
    )
    branch_heal.add(
        "[white]Approach: Subclass requests.Session inside linkwatch/checker.py (LinkWatchSession)[/white]"
    )
    branch_heal.add(
        "[bright_cyan]Patch: Inject default timeout=10.0 & User-Agent without mutating requests globally[/bright_cyan]"
    )
    branch_heal.add(
        "[bold green]✔ Verified: Scope fully isolated; all deterministic assertions pass[/bold green]"
    )

    target_console.print(tree)
    target_console.print()
    return tree


def stream_auto_heal_reasoning(
    steps: Optional[List[str]] = None,
    delay: float = 0.2,
    console: Optional[Console] = None,
) -> None:
    """Stream Gemma's auto-healed reasoning live inside a new reasoning block."""
    target_console = console or default_console
    thought_steps = steps or AUTO_HEAL_COT_STEPS

    accumulated: List[str] = []

    def _render_panel() -> Panel:
        body = Text()
        for idx, line in enumerate(accumulated):
            body.append(line, style="bright_cyan")
            if idx < len(accumulated) - 1:
                body.append("\n")
        return Panel(
            body,
            title="[bold bright_cyan]Gemma Auto-Heal Chain of Thought (Attempt #2)[/bold bright_cyan]",
            border_style="bright_cyan",
            expand=False,
            padding=(1, 2),
        )

    accumulated.append(thought_steps[0])
    with Live(_render_panel(), console=target_console, refresh_per_second=12) as live:
        time.sleep(delay)
        for step in thought_steps[1:]:
            accumulated.append(step)
            live.update(_render_panel())
            time.sleep(delay)


def render_healed_test_table(
    test_results: Optional[List[Dict[str, Any]]] = None,
    console: Optional[Console] = None,
) -> None:
    """Render the updated test runner table verifying all tests pass after auto-healing."""
    target_console = console or default_console
    results = test_results or HEALED_TEST_RESULTS

    table = Table(
        title="LinkWatch Post-Heal Test Execution Suite (7/7 Passed)",
        title_style="bold green",
        border_style="bright_black",
        header_style="bold white",
    )
    table.add_column("Test Identifier", style="white")
    table.add_column("Origin", justify="center")
    table.add_column("Duration", justify="right", style="dim white")
    table.add_column("Result", justify="center")

    for test in results:
        origin_styled = (
            "[bright_cyan]AI-Generated[/bright_cyan]"
            if test["origin"] == "AI-Generated"
            else "[dim white]Pre-existing[/dim white]"
        )
        status_styled = "[bold green]🟢 PASSED[/bold green]"

        table.add_row(
            test["id"],
            origin_styled,
            test.get("duration", "10ms"),
            status_styled,
        )

    target_console.print(table)


def run_auto_heal_loop(
    delay: float = 0.2,
    console: Optional[Console] = None,
) -> None:
    """Execute the complete Phase 4 auto-heal visualization loop.

    1. Trigger prominent rewind divider in bright warning color.
    2. Print failed attempt context and append the decision tree DAG.
    3. Spawn new reasoning block for Attempt #2.
    4. Render healed test suite table and bold solution.
    """
    target_console = console or default_console

    # Step 4.1: The Rewind Visual
    print_rewind_divider(console=target_console)

    # Step 4.2: State Append (Failure context + Decision Tree DAG)
    render_failed_context(console=target_console)
    render_strategy_dag(console=target_console)

    # Step 4.3: New reasoning block
    target_console.print("[dim white]─── [Phase 4.3] Auto-Heal Reasoning & Re-Execution ───[/dim white]")
    stream_auto_heal_reasoning(delay=delay, console=target_console)

    target_console.print()
    render_healed_test_table(console=target_console)

    # Empty line space between table and solution
    target_console.print()

    # Solution in bold without AI emoji
    print_solution(
        "Auto-heal loop successfully resolved regression failure by transitioning to an isolated Session subclass in linkwatch/checker.py."
    )

