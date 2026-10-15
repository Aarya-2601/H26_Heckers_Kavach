"""Dashboard module for Phase 3: The Auditor View & Test Runner Dashboard.

Includes:
- Step 3.1: Chain of Thought Live Panel (streaming Gemma's reasoning in light blue)
- Step 3.2: The Auditor View (Deterministic Auditor checklist updating [ ] to [X])
- Step 3.3: Test Distinction & Status (Table with Pre-existing vs AI-Generated, 🟢/🔴 status, stack trace viewer)
"""

import sys
import time
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.theme import console as default_console

# Ensure UTF-8 output encoding across platforms
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Default Chain of Thought steps for Gemma reasoning
DEFAULT_COT_STEPS: List[str] = [
    "1. Ingesting AST nodes from target repository 'rishrek/LinkWatch'...",
    "2. Inspecting linkwatch/checker.py: detected session.get() without explicit timeout kwarg.",
    "3. Inspecting linkwatch/http_patch.py: detected global mutation of requests.Session.request.",
    "4. Security analysis: missing socket timeouts can cause thread starvation and denial of service.",
    "5. Formulating AST patch: inject timeout=10.0 into fetch() and refactor session adapter.",
    "6. Synthesizing companion test assertions to verify timeout and SSL verification enforcement.",
    "7. AST transformation verified syntactically. Ready for deterministic audit inspection.",
]

# Default checklist items for Deterministic Auditor
DEFAULT_AUDITOR_CHECKS: List[str] = [
    "Checking AST for hardcoded literals and credentials",
    "Scanning for deleted or altered test assertions",
    "Verifying function signature preservation in linkwatch/checker.py",
    "Checking scope isolation: no unvetted global monkey-patching",
    "Ensuring non-root security compliance in Dockerfile",
    "Validating dependency manifest in pyproject.toml and requirements.txt",
]

# Default test results for LinkWatch test runner table
DEFAULT_TEST_RESULTS: List[Dict[str, Any]] = [
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
        "duration": "22ms",
        "status": "PASSED",
    },
    {
        "id": "tests/generated/test_ast_security.py::test_no_global_requests_monkeypatch",
        "origin": "AI-Generated",
        "duration": "15ms",
        "status": "FAILED",
        "stacktrace": """FAILED tests/generated/test_ast_security.py::test_no_global_requests_monkeypatch
Traceback (most recent call last):
  File "tests/generated/test_ast_security.py", line 18, in test_no_global_requests_monkeypatch
    assert requests.Session.request == _original_session_request, (
AssertionError: Global monkey-patch detected in active import scope!
  Target: requests.Session.request was mutated by linkwatch.http_patch:14
  Expected: Clean, unpatched requests.Session without global side-effects.""",
    },
    {
        "id": "tests/generated/test_docker_security.py::test_dockerfile_user_directive",
        "origin": "AI-Generated",
        "duration": "11ms",
        "status": "PASSED",
    },
]


def stream_chain_of_thought(
    steps: Optional[List[str]] = None,
    delay: float = 0.25,
    console: Optional[Console] = None,
) -> None:
    """Stream Gemma's step-by-step reasoning live inside a dedicated panel.

    Enforces the light blue color (bright_cyan) for all text inside this panel.
    """
    target_console = console or default_console
    thought_steps = steps or DEFAULT_COT_STEPS

    accumulated_lines: List[str] = []

    def _render_panel() -> Panel:
        body = Text()
        for idx, line in enumerate(accumulated_lines):
            body.append(line, style="bright_cyan")
            if idx < len(accumulated_lines) - 1:
                body.append("\n")
        return Panel(
            body,
            title="[bold bright_cyan]Gemma Chain of Thought Reasoning[/bold bright_cyan]",
            border_style="bright_cyan",
            expand=False,
            padding=(1, 2),
        )

    # Initial render
    accumulated_lines.append(thought_steps[0])
    with Live(_render_panel(), console=target_console, refresh_per_second=12) as live:
        time.sleep(delay)
        for step in thought_steps[1:]:
            accumulated_lines.append(step)
            live.update(_render_panel())
            time.sleep(delay)


def run_deterministic_auditor(
    checks: Optional[List[str]] = None,
    delay: float = 0.25,
    console: Optional[Console] = None,
) -> None:
    """Render the Deterministic Auditor checklist, updating [ ] to [X] live."""
    target_console = console or default_console
    checklist = checks or DEFAULT_AUDITOR_CHECKS
    total = len(checklist)

    # statuses: False = pending [ ], True = verified [X]
    statuses = [False] * total

    def _render_auditor_panel() -> Panel:
        body = Text()
        for idx, check_item in enumerate(checklist):
            if statuses[idx]:
                body.append("[X] ", style="bold green")
                body.append(f"{check_item}\n", style="white")
            else:
                body.append("[ ] ", style="bright_black")
                body.append(f"{check_item}\n", style="dim white")
        return Panel(
            body,
            title="[bold white]Deterministic Auditor[/bold white]",
            border_style="bright_black",
            expand=False,
            padding=(1, 2),
        )

    with Live(_render_auditor_panel(), console=target_console, refresh_per_second=12) as live:
        time.sleep(delay)
        for i in range(total):
            statuses[i] = True
            live.update(_render_auditor_panel())
            time.sleep(delay)


def render_test_runner_table(
    test_results: Optional[List[Dict[str, Any]]] = None,
    interactive_expand: bool = True,
    console: Optional[Console] = None,
) -> None:
    """Build and display the test runner suite table.

    Origin column: Pre-existing (gray) vs AI-Generated (light blue).
    Result column: 🟢 bold green (PASSED) vs 🔴 bold red (FAILED).
    Prompts "Press [Enter] to view failure details" to display stack traces.
    """
    target_console = console or default_console
    results = test_results or DEFAULT_TEST_RESULTS

    table = Table(
        title="LinkWatch Test Execution Suite",
        title_style="bold white",
        border_style="bright_black",
        header_style="bold white",
    )
    table.add_column("Test Identifier", style="white")
    table.add_column("Origin", justify="center")
    table.add_column("Duration", justify="right", style="dim white")
    table.add_column("Result", justify="center")

    failed_tests: List[Dict[str, Any]] = []

    for test in results:
        # Origin formatting: Pre-existing (gray), AI-Generated (light blue)
        if test["origin"] == "AI-Generated":
            origin_styled = "[bright_cyan]AI-Generated[/bright_cyan]"
        else:
            origin_styled = "[dim white]Pre-existing[/dim white]"

        # Result formatting: 🟢 bold green, 🔴 bold red
        if test["status"] == "PASSED":
            status_styled = "[bold green]🟢 PASSED[/bold green]"
        else:
            status_styled = "[bold red]🔴 FAILED[/bold red]"
            failed_tests.append(test)

        table.add_row(
            test["id"],
            origin_styled,
            test.get("duration", "10ms"),
            status_styled,
        )

    target_console.print(table)
    target_console.print()

    # If there are failed tests, offer failure detail view
    if failed_tests:
        if interactive_expand:
            try:
                # Prompt user to press enter
                input("Press [Enter] to view failure details...")
            except (EOFError, KeyboardInterrupt):
                pass

        target_console.print()
        target_console.print("[dim white]─── Test Failure Details & Stack Trace ───[/dim white]")
        for fail in failed_tests:
            stack = fail.get("stacktrace", "No stack trace provided.")
            panel = Panel(
                Text(stack, style="bold red"),
                title=f"[bold red]Failure Details: {fail['id']}[/bold red]",
                border_style="red",
                expand=False,
            )
            target_console.print(panel)


def run_phase3_dashboard(
    delay: float = 0.2,
    interactive_expand: bool = True,
    console: Optional[Console] = None,
) -> None:
    """Run all Phase 3 dashboard components sequentially."""
    target_console = console or default_console

    target_console.print()
    target_console.print("[dim white]─── [Phase 3.1] Chain of Thought Live Panel ───[/dim white]")
    stream_chain_of_thought(delay=delay, console=target_console)

    target_console.print()
    target_console.print("[dim white]─── [Phase 3.2] The Auditor View ───[/dim white]")
    run_deterministic_auditor(delay=delay, console=target_console)

    target_console.print()
    target_console.print("[dim white]─── [Phase 3.3] Test Distinction & Status Table ───[/dim white]")
    render_test_runner_table(
        interactive_expand=interactive_expand,
        console=target_console,
    )

