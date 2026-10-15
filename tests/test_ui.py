"""Unit tests for UI theming and directory tree visualizer tailored to LinkWatch."""

from rich.tree import Tree
from src.theme import (
    COLOR_AI_OUTPUT,
    COLOR_FLAGGED,
    COLOR_HUMAN_ACTION,
    console,
    custom_theme,
)
from src.visualizer import (
    LINKWATCH_FLAGGED_FILES,
    LINKWATCH_REPO_STRUCTURE,
    build_directory_tree,
    build_tree_from_path,
    render_directory_tree,
)


def test_theme_color_mappings():
    """Verify semantic roles are mapped to expected colors."""
    assert custom_theme.styles["ai"].color.name == "bright_cyan"
    assert custom_theme.styles["human"].color.triplet == (255, 175, 135)
    assert custom_theme.styles["flagged"].bold is True
    assert custom_theme.styles["flagged"].color.name == "red"


def test_build_directory_tree_linkwatch_structure():
    """Verify LinkWatch structure renders with flagged files highlighted."""
    tree = build_directory_tree(
        structure=LINKWATCH_REPO_STRUCTURE,
        flagged_files=LINKWATCH_FLAGGED_FILES,
        root_label="rishrek/LinkWatch",
    )
    assert isinstance(tree, Tree)

    with console.capture() as capture:
        console.print(tree)
    output = capture.get()

    assert "LinkWatch" in output
    assert "http_patch.py" in output
    assert "checker.py" in output
    assert "Dockerfile" in output
    assert "sites.toml" in output


def test_render_directory_tree_from_dataset_path():
    """Verify tree builds successfully from actual LinkWatch dataset path if present."""
    tree = render_directory_tree(source_path="dataset/LinkWatch")
    assert isinstance(tree, Tree)
    assert len(tree.children) > 0
