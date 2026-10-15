"""Main entry point for CLI UI demonstration tailored to rishrek/LinkWatch.

Phase 1: Foundation, Theming & Directory Tree
- Step 1.1: Color System & Rich Console Setup:
    * AI outputs -> light blue (bright_cyan)
    * Human inputs/actions -> peachy-orange (rgb(255,175,135))
- Step 1.2: Directory & AST Visualizer using rich.tree.Tree:
    * Target Dataset: rishrek/LinkWatch (website uptime & link checker)
    * Flagged security/AST audit files in bold red
    * Neutral files and directories in neutral gray or white
- Step 1.3: Verify terminal outputs LinkWatch directory tree with flagged files in bold red
"""

from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.theme import console, print_ai, print_human
from src.visualizer import (
    LINKWATCH_FLAGGED_FILES,
    LINKWATCH_REPO_STRUCTURE,
    render_directory_tree,
)


def main() -> None:
    # Header panel showcasing LinkWatch audit demo & visual identity
    header_text = Text()
    header_text.append("LinkWatch CLI Security & AST Visualizer\n", style="bold white")
    header_text.append("Dataset Target: https://github.com/rishrek/LinkWatch\n", style="bright_cyan")
    header_text.append("Phase 1: Theming System & Flagged Directory Tree", style="dim white")
    console.print(Panel(header_text, border_style="bright_black", expand=False))

    console.print()

    # Step 1.1: Demonstrate Color System & Console Mapping
    console.print("[dim white]─── [Step 1.1] Color System & Theming Palette ───[/dim white]")
    print_ai("🤖 AI Output: Ingesting repository dataset 'rishrek/LinkWatch' (website & link uptime checker)...")
    print_human("👤 Human Action: Selected rishrek/LinkWatch for AST inspection & security audit.")
    print_ai("🤖 AI Output: AST scanner parsed 26 files across linkwatch/, tests/, and root manifests.")
    print_human("👤 Human Action: Confirmed flagged files for review: http_patch.py, checker.py, Dockerfile.")

    console.print()

    # Step 1.2 & 1.3: Render LinkWatch Directory Tree with Flagged Files in bold red
    console.print("[dim white]─── [Step 1.2 & 1.3] LinkWatch Directory & Flagged AST Tree ───[/dim white]")
    console.print(
        f"[dim white]Flagged files ({len(LINKWATCH_FLAGGED_FILES)}):[/dim white] "
        + ", ".join(f"[bold red]{f}[/bold red]" for f in sorted(LINKWATCH_FLAGGED_FILES))
    )
    console.print()

    # Check if real dataset folder exists; use it if available, otherwise use structural dict
    dataset_path = Path("dataset/LinkWatch")
    source_path = dataset_path if dataset_path.exists() else None

    # Render tree
    render_directory_tree(
        structure=LINKWATCH_REPO_STRUCTURE,
        flagged_files=LINKWATCH_FLAGGED_FILES,
        root_label="rishrek/LinkWatch",
        console=console,
        source_path=source_path,
    )

    console.print()

    # Flagged security audit findings summary table
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
    console.print()
    print_ai("✨ LinkWatch directory tree rendered successfully with flagged vulnerabilities.")


if __name__ == "__main__":
    main()
