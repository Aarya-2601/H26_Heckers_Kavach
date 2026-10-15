"""CLI Foundation, Theming, Visualizer, Interactive Voice & Phase 3 Dashboard.

Tailored for rishrek/LinkWatch dataset and AST security demonstration.
"""

from src.dashboard import (
    DEFAULT_AUDITOR_CHECKS,
    DEFAULT_COT_STEPS,
    DEFAULT_TEST_RESULTS,
    render_test_runner_table,
    run_deterministic_auditor,
    run_phase3_dashboard,
    stream_chain_of_thought,
)
from src.prompts import (
    DEFAULT_DEPENDENCY_CHOICES,
    DEFAULT_FLAGGED_CHOICES,
    INPUT_METHOD_CHOICES,
    PEACHY_ORANGE_HEX,
    custom_questionary_style,
    prompt_remediation_input,
    prompt_select_dependency,
    prompt_select_flagged_file,
    prompt_select_input_method,
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
    print_solution,
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
    "print_solution",
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
    "INPUT_METHOD_CHOICES",
    "DEFAULT_COT_STEPS",
    "DEFAULT_AUDITOR_CHECKS",
    "DEFAULT_TEST_RESULTS",
    "build_directory_tree",
    "build_tree_from_path",
    "render_directory_tree",
    "VoiceInputWrapper",
    "capture_voice_input",
    "voice_wrapper",
    "prompt_select_dependency",
    "prompt_select_flagged_file",
    "prompt_select_input_method",
    "prompt_remediation_input",
    "run_interactive_workflow",
    "stream_chain_of_thought",
    "run_deterministic_auditor",
    "render_test_runner_table",
    "run_phase3_dashboard",
]
