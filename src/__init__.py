"""CLI Foundation, Theming & Directory Visualizer Package.

Tailored for rishrek/LinkWatch dataset and AST security demonstration.
"""

from src.theme import (
    COLOR_AI_OUTPUT,
    COLOR_FLAGGED,
    COLOR_HUMAN_ACTION,
    COLOR_NEUTRAL_GRAY,
    COLOR_NEUTRAL_WHITE,
    console,
    custom_theme,
    print_ai,
    print_human,
)
from src.visualizer import (
    DEFAULT_DUMMY_FLAGGED,
    DEFAULT_DUMMY_REPO,
    LINKWATCH_FLAGGED_FILES,
    LINKWATCH_REPO_STRUCTURE,
    build_directory_tree,
    build_tree_from_path,
    render_directory_tree,
)

__all__ = [
    "console",
    "custom_theme",
    "print_ai",
    "print_human",
    "COLOR_AI_OUTPUT",
    "COLOR_HUMAN_ACTION",
    "COLOR_FLAGGED",
    "COLOR_NEUTRAL_WHITE",
    "COLOR_NEUTRAL_GRAY",
    "LINKWATCH_REPO_STRUCTURE",
    "LINKWATCH_FLAGGED_FILES",
    "DEFAULT_DUMMY_REPO",
    "DEFAULT_DUMMY_FLAGGED",
    "build_directory_tree",
    "build_tree_from_path",
    "render_directory_tree",
]
