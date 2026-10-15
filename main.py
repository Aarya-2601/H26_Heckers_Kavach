"""Main entry point for CLI UI demonstration.

Phase 1: Foundation, Theming & Directory Tree
- Step 1.1: Color System & Rich Console Setup (AI light blue bright_cyan, Human peachy-orange rgb(255,175,135))
- Step 1.2: Directory & AST Visualizer using rich.tree.Tree with flagged files in bold red
- Step 1.3: Verify terminal outputs fake directory tree with flagged files in bold red
"""

from rich.panel import Panel
from rich.text import Text

from src.theme import console, print_ai, print_human
from src.visualizer import DEFAULT_DUMMY_FLAGGED, DEFAULT_DUMMY_REPO, render_directory_tree


def main() -> None:
    # Header panel showcasing foundation and theme
    header_text = Text()
    header_text.append("CLI Visual Foundation & Theming Engine\n", style="bold white")
    header_text.append("Phase 1: Color Palette Mapping & Flagged Directory Tree Visualizer", style="dim white")
    console.print(Panel(header_text, border_style="bright_black", expand=False))

    console.print()

    # Step 1.1: Demonstrate Color System & Console Mapping
    console.print("[dim white]─── Theme Palette Verification ───[/dim white]")
    print_ai("🤖 AI Output: Analyzing repository structure and AST vulnerabilities...")
    print_human("👤 Human Action: Flagged suspicious files for manual security review.")

    console.print()

    # Step 1.2 & 1.3: Render Fake Directory Tree with Flagged Files in bold red
    console.print("[dim white]─── Repository Structure & Flagged AST Visualizer ───[/dim white]")
    console.print(
        f"[dim white]Flagged files to highlight ({len(DEFAULT_DUMMY_FLAGGED)}):[/dim white] "
        + ", ".join(f"[bold red]{f}[/bold red]" for f in sorted(DEFAULT_DUMMY_FLAGGED))
    )
    console.print()

    # Render tree
    render_directory_tree(
        structure=DEFAULT_DUMMY_REPO,
        flagged_files=DEFAULT_DUMMY_FLAGGED,
        root_label="project-root",
        console=console,
    )

    console.print()
    print_ai("✨ Tree visualizer successfully rendered with flagged security alerts.")


if __name__ == "__main__":
    main()
