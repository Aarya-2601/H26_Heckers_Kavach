"""CLI Foundation, Theming, Visualizer & Interactive Voice Package.

Tailored for rishrek/LinkWatch dataset and AST security demonstration.
"""

from src.prompts import (
    DEFAULT_DEPENDENCY_CHOICES,
    DEFAULT_FLAGGED_CHOICES,
    PEACHY_ORANGE_HEX,
    custom_questionary_style,
    prompt_remediation_input,
    prompt_select_dependency,
    prompt_select_flagged_file,
    run_interactive_workflow,
)
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
from src.voice import VoiceInputWrapper, capture_voice_input, voice_wrapper

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
    "PEACHY_ORANGE_HEX",
    "custom_questionary_style",
    "LINKWATCH_REPO_STRUCTURE",
    "LINKWATCH_FLAGGED_FILES",
    "DEFAULT_DUMMY_REPO",
    "DEFAULT_DUMMY_FLAGGED",
    "DEFAULT_DEPENDENCY_CHOICES",
    "DEFAULT_FLAGGED_CHOICES",
    "build_directory_tree",
    "build_tree_from_path",
    "render_directory_tree",
    "VoiceInputWrapper",
    "capture_voice_input",
    "voice_wrapper",
    "prompt_select_dependency",
    "prompt_select_flagged_file",
    "prompt_remediation_input",
    "run_interactive_workflow",
]
