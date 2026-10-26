"""Unit tests for UI theming, visualizer, prompts, voice, dashboard, auto-heal loop, and CAPSULE generator."""

from pathlib import Path
from rich.tree import Tree
from src.auto_heal import (
    AUTO_HEAL_COT_STEPS,
    HEALED_TEST_RESULTS,
    print_rewind_divider,
    render_failed_context,
    render_healed_test_table,
    render_strategy_dag,
    stream_auto_heal_reasoning,
)
from src.capsule import (
    generate_capsule_markdown,
    generate_mermaid_diagram,
    write_capsule_file,
)
from src.dashboard import (
    DEFAULT_AUDITOR_CHECKS,
    DEFAULT_COT_STEPS,
    DEFAULT_TEST_RESULTS,
    render_test_runner_table,
    run_deterministic_auditor,
    stream_chain_of_thought,
)
from src.prompts import (
    DEFAULT_DEPENDENCY_CHOICES,
    DEFAULT_FLAGGED_CHOICES,
    INPUT_METHOD_CHOICES,
    PEACHY_ORANGE_HEX,
    custom_questionary_style,
)
from src.theme import (
    COLOR_AI_OUTPUT,
    COLOR_FLAGGED,
    COLOR_HUMAN_ACTION,
    console,
    custom_theme,
    print_solution,
)
from src.visualizer import (
    build_directory_tree,
    render_directory_tree,
)
from src.voice import VoiceInputWrapper, capture_voice_input

# Generic sample repository used by the tests (no real project is assumed)
SAMPLE_REPO_STRUCTURE = {
    "app": {
        "__init__.py": None,
        "client.py": None,
        "config.py": None,
    },
    "tests": {
        "test_client.py": None,
        "test_config.py": None,
    },
    "Dockerfile": None,
    "README.md": None,
    "requirements.txt": None,
    "settings.toml": None,
}
SAMPLE_FLAGGED_FILES = {"client.py", "Dockerfile"}


def test_theme_color_mappings():
    """Verify semantic roles are mapped to expected colors."""
    assert custom_theme.styles["ai"].color.name == "bright_cyan"
    assert custom_theme.styles["human"].color.triplet == (255, 175, 135)
    assert custom_theme.styles["flagged"].bold is True
    assert custom_theme.styles["flagged"].color.name == "red"


def test_solution_styling_is_bold():
    """Verify print_solution outputs bold text without ai emoji."""
    with console.capture() as capture:
        print_solution("Replace requests with httpx in app/client.py")
    output = capture.get()

    assert "Solution:" in output
    assert "Replace requests with httpx" in output
    assert "🤖" not in output


def test_build_directory_tree_sample_structure():
    """Verify a sample structure renders with flagged files highlighted."""
    tree = build_directory_tree(
        structure=SAMPLE_REPO_STRUCTURE,
        flagged_files=SAMPLE_FLAGGED_FILES,
        root_label="example/sample-repo",
    )
    assert isinstance(tree, Tree)

    with console.capture() as capture:
        console.print(tree)
    output = capture.get()

    assert "sample-repo" in output
    assert "client.py" in output
    assert "Dockerfile" in output
    assert "settings.toml" in output


def test_questionary_peachy_orange_styling():
    """Verify Questionary prompt styling uses the peachy-orange hex code #ffaf87."""
    assert PEACHY_ORANGE_HEX.lower() == "#ffaf87"

    rule_map = dict(custom_questionary_style.style_rules)
    assert "qmark" in rule_map
    assert "fg:#ffaf87" in rule_map["qmark"]
    assert "question" in rule_map
    assert "fg:#ffaf87" in rule_map["question"]
    assert "answer" in rule_map
    assert "fg:#ffaf87" in rule_map["answer"]


def test_questionary_choices():
    """Verify fallback selection menus offer a custom entry and input modes are present."""
    assert any("custom" in choice.lower() for choice in DEFAULT_DEPENDENCY_CHOICES)
    assert any("custom" in choice.lower() for choice in DEFAULT_FLAGGED_CHOICES)
    assert any("Voice" in choice for choice in INPUT_METHOD_CHOICES)
    assert any("Manual" in choice for choice in INPUT_METHOD_CHOICES)


def test_voice_wrapper_mock_and_fallback():
    """Verify VoiceInputWrapper handles mock input and fallback text gracefully."""
    wrapper = VoiceInputWrapper()

    # Test mock transcription
    mock_res = wrapper.listen_and_transcribe(
        mock_input="replace requests with httpx in app/client.py"
    )
    assert mock_res == "replace requests with httpx in app/client.py"

    # Test convenience helper
    convenience_res = capture_voice_input(
        mock_input="refactor client.py monkey patch"
    )
    assert convenience_res == "refactor client.py monkey patch"


def test_stream_chain_of_thought():
    """Verify CoT live panel streams steps with light blue styling."""
    with console.capture() as capture:
        stream_chain_of_thought(steps=["Step 1: Test CoT step"], delay=0.01, console=console)
    output = capture.get()
    assert "Gemma Chain of Thought Reasoning" in output
    assert "Step 1: Test CoT step" in output


def test_run_deterministic_auditor():
    """Verify Deterministic Auditor renders checklist items with [X] status."""
    with console.capture() as capture:
        run_deterministic_auditor(checks=["Checking AST for hardcoded literals"], delay=0.01, console=console)
    output = capture.get()
    assert "Deterministic Auditor" in output
    assert "[X]" in output
    assert "Checking AST for hardcoded literals" in output


def test_render_test_runner_table():
    """Verify test table correctly labels Pre-existing vs AI-Generated and PASSED/FAILED."""
    with console.capture() as capture:
        render_test_runner_table(
            test_results=DEFAULT_TEST_RESULTS,
            interactive_expand=False,
            console=console,
        )
    output = capture.get()
    assert "Test Execution Suite" in output
    assert "Pre-existing" in output
    assert "AI-Generated" in output
    assert "PASSED" in output
    assert "FAILED" in output
    assert "test_no_global_state_mutation" in output


def test_rewind_divider():
    """Verify rewind divider prints prominent warning header without clearing terminal."""
    with console.capture() as capture:
        print_rewind_divider(console=console)
    output = capture.get()
    assert "REWIND: TRIGGERING AUTO-HEAL LOOP" in output


def test_failed_context_and_strategy_dag():
    """Verify failed context and decision tree DAG illustrate abandoned and active branches."""
    with console.capture() as capture:
        render_failed_context(console=console)
        render_strategy_dag(console=console)
    output = capture.get()

    assert "Failed Attempt Diagnostics" in output
    assert "Auto-Heal Search Tree & Decision DAG" in output
    assert "Attempt #1:" in output and "ABANDONED" in output
    assert "Attempt #2:" in output and "ACTIVE" in output and "SELECTED" in output


def test_healed_test_table():
    """Verify post-heal test table shows all tests passed."""
    with console.capture() as capture:
        render_healed_test_table(console=console)
    output = capture.get()

    assert "Post-Heal Test Execution Suite" in output
    total = len(HEALED_TEST_RESULTS)
    assert f"{total}/{total} Passed" in output
    assert "FAILED" not in output


def test_generate_mermaid_diagram():
    """Verify Mermaid diagram syntax contains standard graph TD structure."""
    mermaid = generate_mermaid_diagram()
    assert "```mermaid" in mermaid
    assert "graph TD" in mermaid
    assert "Attempt #1" in mermaid
    assert "Rewind: Trigger Auto-Heal Loop" in mermaid
    assert "Attempt #2" in mermaid
    assert "All Tests Passed" in mermaid


def test_generate_capsule_markdown_strict_separation():
    """Verify CAPSULE.md maintains strict separation between AI reasoning and telemetry."""
    doc = generate_capsule_markdown(repo_target="https://github.com/example/sample-repo")

    # Verify key sections
    assert "1. Execution Path & Auto-Heal Topology" in doc
    assert "2. AI Reasoning Layer (Cognitive Trace)" in doc
    assert "3. Ground-Truth Telemetry Layer (Deterministic Verifications)" in doc
    assert "```mermaid" in doc

    # Verify AST metrics and test logs
    assert "AST & Codebase Metrics" in doc
    assert "Deterministic Auditor Checklist" in doc
    assert "Test Suite Execution Logs" in doc
    assert "example/sample-repo" in doc


def test_write_capsule_file(tmp_path: Path):
    """Verify write_capsule_file writes the artifact to disk successfully."""
    target_file = tmp_path / "CAPSULE_TEST.md"
    written_path = write_capsule_file(output_path=str(target_file), console=console)
    assert written_path.exists()
    content = written_path.read_text(encoding="utf-8")
    assert "# 🛡️ CAPSULE:" in content
    assert "```mermaid" in content


def test_dynamic_auto_heal_cot_generation():
    """Verify auto-heal CoT steps dynamically change based on target dependency."""
    from src.auto_heal import build_auto_heal_cot_steps

    steps_appdirs = build_auto_heal_cot_steps("appdirs", "platformdirs", "app/cache.py")
    assert any("platformdirs" in s for s in steps_appdirs)
    assert not any("requests.Session" in s for s in steps_appdirs)

    steps_toml = build_auto_heal_cot_steps("toml", "tomllib", "app/config.py")
    assert any("tomllib" in s for s in steps_toml)
    assert not any("platformdirs" in s for s in steps_toml)

    steps_jinja = build_auto_heal_cot_steps("jinja2", "jinja2-modern", "app/report.py")
    assert any("soft_unicode" in s or "markupsafe" in s for s in steps_jinja)

    steps_req = build_auto_heal_cot_steps("requests", "httpx", "app/client.py")
    assert any("Session" in s for s in steps_req)


def test_dynamic_capsule_markdown():
    """Verify CAPSULE.md text is dynamic for different packages."""
    doc_appdirs = generate_capsule_markdown(target_package="appdirs", replacement_pkg="platformdirs", hero_file="app/cache.py")
    assert "appdirs" in doc_appdirs
    assert "platformdirs" in doc_appdirs
    assert "cache-directory environment variable" in doc_appdirs
    assert "app/cache.py" in doc_appdirs

    doc_toml = generate_capsule_markdown(target_package="toml", replacement_pkg="tomllib", hero_file="app/config.py")
    assert "tomllib" in doc_toml
    assert "open(path, \"rb\")" in doc_toml