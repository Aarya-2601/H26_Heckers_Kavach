"""Directory and AST Visualizer module.

Renders repository structures with flagged files styled in bold red,
leaving non-flagged files and directories in neutral gray or white.
"""

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Union
from rich.tree import Tree
from rich.console import Console

from src.theme import console as default_console

# Generic empty defaults (kept so existing imports of these names still work)
DEFAULT_DUMMY_REPO: Dict[str, Any] = {}
DEFAULT_DUMMY_FLAGGED: Set[str] = set()


def _is_flagged(name: str, rel_path: str, flagged_set: Set[str]) -> bool:
    """Check if a file matches any flagged entry by filename or relative path."""
    if name in flagged_set:
        return True
    if rel_path in flagged_set:
        return True
    norm_rel = rel_path.replace("\\", "/")
    for flag in flagged_set:
        norm_flag = flag.replace("\\", "/")
        if norm_rel == norm_flag or norm_rel.endswith("/" + norm_flag):
            return True
    return False


def build_directory_tree(
    structure: Optional[Dict[str, Any]] = None,
    flagged_files: Optional[Iterable[str]] = None,
    root_label: str = "repo",
) -> Tree:
    """Build a rich.tree.Tree representing a repository structure.

    Args:
        structure: Nested dictionary where keys are folder/file names and values are
                   nested dicts (for directories) or None (for files). Defaults to an empty tree.
        flagged_files: Collection of file names or paths that should be highlighted.
                       Defaults to no flagged files.
        root_label: Label for the root node.

    Returns:
        A rich.tree.Tree instance with flagged files styled in bold red and
        neutral files/folders styled in neutral gray or white.
    """
    if structure is None:
        structure = {}

    flagged_set = set(flagged_files) if flagged_files is not None else set()

    # Root in bold white, guide style in neutral gray
    tree = Tree(f"[bold white]{root_label}/[/bold white]", guide_style="bright_black")

    def _populate_node(parent_node: Tree, current_dict: Dict[str, Any], current_path: str) -> None:
        # Separate directories and files for organized rendering
        items = sorted(current_dict.items(), key=lambda item: (item[1] is None, item[0].lower()))

        for name, contents in items:
            node_path = f"{current_path}/{name}" if current_path else name
            if isinstance(contents, dict):
                # Directory node: neutral white
                dir_node = parent_node.add(f"[white]{name}/[/white]")
                _populate_node(dir_node, contents, node_path)
            else:
                # File node: bold red if flagged, neutral gray/white otherwise
                if _is_flagged(name, node_path, flagged_set):
                    parent_node.add(f"[bold red]{name}[/bold red]")
                else:
                    parent_node.add(f"[dim white]{name}[/dim white]")

    _populate_node(tree, structure, "")
    return tree


def build_tree_from_path(
    root_path: Union[str, Path],
    flagged_files: Optional[Iterable[str]] = None,
    max_depth: int = 5,
    root_label: Optional[str] = None,
) -> Tree:
    """Build a rich.tree.Tree from an actual filesystem directory (e.g. a cloned repo).

    Args:
        root_path: Path to the directory to inspect.
        flagged_files: Collection of file names or paths to flag.
        max_depth: Maximum directory recursion depth.
        root_label: Custom label for the root node.
    """
    path = Path(root_path).resolve()
    flagged_set = set(flagged_files) if flagged_files is not None else set()
    display_name = root_label or path.name

    tree = Tree(f"[bold white]{display_name}/[/bold white]", guide_style="bright_black")

    def _walk(current_path: Path, current_node: Tree, depth: int) -> None:
        if depth > max_depth:
            current_node.add("[bright_black]... (max depth)[/bright_black]")
            return

        try:
            entries = sorted(current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            current_node.add("[bright_black][access denied][/bright_black]")
            return

        for entry in entries:
            # Skip hidden git files or caches
            if entry.name in {".git", "__pycache__", ".pytest_cache"}:
                continue

            rel_str = str(entry.relative_to(path))
            if entry.is_dir():
                sub_node = current_node.add(f"[white]{entry.name}/[/white]")
                _walk(entry, sub_node, depth + 1)
            else:
                if _is_flagged(entry.name, rel_str, flagged_set):
                    current_node.add(f"[bold red]{entry.name}[/bold red]")
                else:
                    current_node.add(f"[dim white]{entry.name}[/dim white]")

    _walk(path, tree, 1)
    return tree


def render_directory_tree(
    structure: Optional[Dict[str, Any]] = None,
    flagged_files: Optional[Iterable[str]] = None,
    root_label: Optional[str] = None,
    console: Optional[Console] = None,
    source_path: Optional[Union[str, Path]] = None,
) -> Tree:
    """Render and print a repository directory tree to the console.

    Args:
        structure: Nested dictionary structure (defaults to an empty tree).
        flagged_files: Collection of file names to highlight in bold red.
        root_label: Display name for the tree root (defaults to the folder name, or 'repo' for a dict).
        console: rich.console.Console instance to print to. Defaults to custom theme console.
        source_path: Optional filesystem path (e.g. a cloned repo directory).

    Returns:
        The generated rich.tree.Tree instance.
    """
    target_console = console or default_console

    if source_path is not None and Path(source_path).exists():
        tree = build_tree_from_path(
            root_path=source_path,
            flagged_files=flagged_files,
            root_label=root_label,
        )
    else:
        tree = build_directory_tree(
            structure=structure,
            flagged_files=flagged_files,
            root_label=root_label or "repo",
        )

    target_console.print(tree)
    return tree