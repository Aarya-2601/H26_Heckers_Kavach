"""Main CLI application entry point.

Phase 1: Foundation, Theming & Directory Tree
- Color System: AI light blue (bright_cyan), Human peachy-orange (rgb(255,175,135) / #ffaf87)
- LinkWatch Directory & AST Visualizer with flagged files in bold red

Phase 2: Interactive Inputs & Voice Capture
- Step 2.1: Terminal Prompts using questionary (styled in peachy-orange #ffaf87)
- Step 2.2: Dynamic voice capture with 5s silence wait (optional)
- Step 2.3: Solutions formatted in bold with one-line space after prompt

Phase 3: The Auditor View & Test Runner Dashboard
- Step 3.1: Chain of Thought Live Panel (streaming Gemma's reasoning in bright_cyan)
- Step 3.2: The Auditor View (Deterministic Auditor checklist updating [ ] to [X])
- Step 3.3: Test Distinction & Status (Table with Pre-existing vs AI-Generated, 🟢/🔴 status, stack trace viewer)
"""

import argparse
import sys
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.dashboard import (
    render_test_runner_table,
    run_deterministic_auditor,
    run_phase3_dashboard,
    stream_chain_of_thought,
)
from src.prompts import (
    DEFAULT_DEPENDENCY_CHOICES,
    DEFAULT_FLAGGED_CHOICES,
    INPUT_METHOD_CHOICES,
    prompt_remediation_input,
    prompt_select_dependency,
    prompt_select_flagged_file,
    prompt_select_input_method,
    run_interactive_workflow,
)
from src.theme import console, print_ai, print_human, print_solution
from src.visualizer import (
    LINKWATCH_FLAGGED_FILES,
    LINKWATCH_REPO_STRUCTURE,
    render_directory_tree,
)
from src.voice import capture_voice_input


def run_phase1_visualizer() -> None:
    """Render Phase 1 visual foundation, theming, and LinkWatch directory tree."""
    header_text = Text()
    header_text.append("LinkWatch CLI Security & AST Remediator\n", style="bold white")
    header_text.append("Dataset Target: https://github.com/rishrek/LinkWatch\n", style="bright_cyan")
    header_text.append("Phase 1: Theme & AST Tree | Phase 2: Interactive & Voice | Phase 3: Auditor & Tests", style="dim white")
    console.print(Panel(header_text, border_style="bright_black", expand=False))

    console.print()

    # Step 1.1: Color System & Theming Palette
    console.print("[dim white]─── [Phase 1.1] Color System & Theming Palette ───[/dim white]")
    print_ai("AI Output: Ingesting repository dataset 'rishrek/LinkWatch' (website & link uptime checker)...")
    print_human("Human Action: Selected rishrek/LinkWatch for AST inspection & security audit.")
    print_ai("AI Output: AST scanner parsed 26 files across linkwatch/, tests/, and root manifests.")
    print_human("Human Action: Confirmed flagged files for review: http_patch.py, checker.py, Dockerfile.")

    console.print()

    # Step 1.2 & 1.3: LinkWatch Directory Tree with Flagged Files in bold red
    console.print("[dim white]─── [Phase 1.2 & 1.3] LinkWatch Directory & Flagged AST Tree ───[/dim white]")
    console.print(
        f"[dim white]Flagged files ({len(LINKWATCH_FLAGGED_FILES)}):[/dim white] "
        + ", ".join(f"[bold red]{f}[/bold red]" for f in sorted(LINKWATCH_FLAGGED_FILES))
    )
    console.print()

    dataset_path = Path("dataset/LinkWatch")
    source_path = dataset_path if dataset_path.exists() else None

    render_directory_tree(
        structure=LINKWATCH_REPO_STRUCTURE,
        flagged_files=LINKWATCH_FLAGGED_FILES,
        root_label="rishrek/LinkWatch",
        console=console,
        source_path=source_path,
    )

    console.print()

    # Findings summary table
    summary_table = Table(
        title="LinkWatch Flagged Security & AST Findings",
        title_style="bold white",
        border_style="bright_black",
        header_style="bold white",
    )
    summary_table.add_column("Flagged File", style="bold red")
    summary_table.add_column("Category", style="bright_cyan")
    summary_table.add_column("Security / AST Rationale", style="dim white")

    summary_table.add_row(
        "http_patch.py",
        "Runtime Monkey-Patch",
        "Directly mutates requests.Session.request globally at import time",
    )
    summary_table.add_row(
        "checker.py",
        "Missing Network Timeout",
        "session.get() called without explicit timeout; potential DoS hang",
    )
    summary_table.add_row(
        "Dockerfile",
        "Privileged Execution",
        "Container runs as root user without dedicated non-root USER instruction",
    )

    console.print(summary_table)


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkWatch CLI Security & Interactive Voice Remediator")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without interactive prompts (for CI/automated testing)",
    )
    parser.add_argument(
        "--mock-voice",
        type=str,
        default=None,
        help="Provide mock voice input text to bypass microphone hardware in testing",
    )
    parser.add_argument(
        "--voice",
        dest="voice",
        action="store_true",
        default=None,
        help="Force enable voice capture step",
    )
    parser.add_argument(
        "--no-voice",
        dest="voice",
        action="store_false",
        help="Skip microphone listening step and use manual typing",
    )
    args = parser.parse_args()

    # Run Phase 1: Foundation & Directory Visualizer
    run_phase1_visualizer()

    # Run Phase 2: Interactive Inputs & Voice Capture
    if args.non_interactive:
        console.print()
        console.print("[dim white]─── [Phase 2] Non-interactive verification mode ───[/dim white]")
        mock_text = args.mock_voice or "replace requests with httpx in linkwatch/checker.py"
        print_ai("AI Output: Non-interactive mode engaged. Skipping live stdin prompts.")
        print_human(f"Simulated Action: {mock_text}")
        console.print()
        print_solution(f"Scheduled remediation AST rewrite with action: '{mock_text}'.")
    else:
        is_tty = sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty()
        if not is_tty and args.mock_voice is None:
            console.print()
            console.print("[dim white]⚠️  Non-interactive terminal detected (no TTY). Proceeding to Dashboard.[/dim white]")
        else:
            run_interactive_workflow(
                listen_voice=args.voice,
                mock_voice_text=args.mock_voice,
            )

    # Run Phase 3: The Auditor View & Test Runner Dashboard
    delay = 0.05 if args.non_interactive else 0.2
    run_phase3_dashboard(
        delay=delay,
        interactive_expand=not args.non_interactive,
        console=console,
    )


if __name__ == "__main__":
    main()
