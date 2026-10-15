"""Unit tests for UI theming, visualizer, questionary prompts, and voice input."""

from rich.tree import Tree
from src.prompts import (
    DEFAULT_DEPENDENCY_CHOICES,
    DEFAULT_FLAGGED_CHOICES,
    PEACHY_ORANGE_HEX,
    custom_questionary_style,
)
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
    render_directory_tree,
)
from src.voice import VoiceInputWrapper, capture_voice_input


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


def test_questionary_peachy_orange_styling():
    """Verify Questionary prompt styling uses the peachy-orange hex code #ffaf87."""
    assert PEACHY_ORANGE_HEX.lower() == "#ffaf87"

    # Verify style dictionary contains peachy-orange rules for prompt text and markers
    rule_map = dict(custom_questionary_style.style_rules)
    assert "qmark" in rule_map
    assert "fg:#ffaf87" in rule_map["qmark"]
    assert "question" in rule_map
    assert "fg:#ffaf87" in rule_map["question"]
    assert "answer" in rule_map
    assert "fg:#ffaf87" in rule_map["answer"]


def test_questionary_choices():
    """Verify selection menus contain expected LinkWatch audit options."""
    assert any("requests" in choice for choice in DEFAULT_DEPENDENCY_CHOICES)
    assert any("http_patch.py" in choice for choice in DEFAULT_FLAGGED_CHOICES)


def test_voice_wrapper_mock_and_fallback():
    """Verify VoiceInputWrapper handles mock input and fallback text gracefully."""
    wrapper = VoiceInputWrapper()

    # Test mock transcription
    mock_res = wrapper.listen_and_transcribe(
        mock_input="replace requests with httpx in linkwatch/checker.py"
    )
    assert mock_res == "replace requests with httpx in linkwatch/checker.py"

    # Test convenience helper
    convenience_res = capture_voice_input(
        mock_input="refactor http_patch.py monkey patch"
    )
    assert convenience_res == "refactor http_patch.py monkey patch"
