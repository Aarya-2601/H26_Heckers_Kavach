"""Unit tests for UI theming and directory tree visualizer."""

from rich.tree import Tree
from src.theme import (
    COLOR_AI_OUTPUT,
    COLOR_FLAGGED,
    COLOR_HUMAN_ACTION,
    console,
    custom_theme,
)
from src.visualizer import (
    DEFAULT_DUMMY_FLAGGED,
    DEFAULT_DUMMY_REPO,
    build_directory_tree,
    render_directory_tree,
)


def test_theme_color_mappings():
    """Verify semantic roles are mapped to expected colors."""
    assert custom_theme.styles["ai"].color.name == "bright_cyan"
    assert custom_theme.styles["human"].color.triplet == (255, 175, 135)
    assert custom_theme.styles["flagged"].bold is True
    assert custom_theme.styles["flagged"].color.name == "red"


def test_build_directory_tree_renders_flagged_files():
    """Verify build_directory_tree tags flagged files in bold red and others in neutral."""
    flagged = {"routes.py", "crypto.py"}
    structure = {
        "src": {
            "routes.py": None,
            "helpers.py": None,
        }
    }
    tree = build_directory_tree(structure=structure, flagged_files=flagged, root_label="test-repo")
    assert isinstance(tree, Tree)

    # Convert tree structure to string representation
    with console.capture() as capture:
        console.print(tree)
    output = capture.get()

    assert "test-repo" in output
    assert "routes.py" in output
    assert "helpers.py" in output


def test_render_directory_tree_default():
    """Verify default dummy repo renders cleanly with default console."""
    tree = render_directory_tree()
    assert isinstance(tree, Tree)
    assert len(tree.children) > 0
