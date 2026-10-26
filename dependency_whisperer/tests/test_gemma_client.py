"""
Tests for Gemma 4 Client & Deterministic Mock Engine.
"""

from dependency_whisperer.gemma_client import GemmaClient, GemmaModelMetadata
from dependency_whisperer.schemas import ReplacementRecommendation, TestSuitePlan


def test_client_initialization_defaults():
    client = GemmaClient(backend="mock")
    assert client.metadata.model_name == "gemma-4-it"
    assert client.backend == "mock"
    assert "Google Gemma" in client.metadata.applicable_terms


def test_json_extraction():
    client = GemmaClient(backend="mock")
    markdown_fence = "```json\n{\"key\": \"value\"}\n```"
    assert client.extract_json(markdown_fence) == "{\"key\": \"value\"}"

    embedded = "Here is the result: {\"status\": \"ok\"} Thanks!"
    assert client.extract_json(embedded) == "{\"status\": \"ok\"}"


def test_mock_engine_triage_structured():
    client = GemmaClient(backend="mock")
    prompt = "Triage target dependency: toml"
    result = client.generate_structured(prompt, ReplacementRecommendation)
    assert result.target_dependency == "toml"
    assert result.recommended_choice == "tomllib"
    assert len(result.options) >= 2


# ---------------------------------------------------------------------------
# The mock must be repository-agnostic: derive answers from the prompt, never
# return text written for some other project.
# ---------------------------------------------------------------------------
import subprocess
import sys

import pytest

from dependency_whisperer.gemma_client import GemmaBackendError
from dependency_whisperer.whisperer import DependencyWhisperer

ARBITRARY_CODE = (
    "import os\n"
    "import frobnicate\n\n\n"
    "def add(a, b=1):\n"
    "    return frobnicate.plus(a, b)\n\n\n"
    "class Box:\n"
    "    pass\n"
)


def _whisperer():
    return DependencyWhisperer(client=GemmaClient(backend="mock"))


def test_mock_triage_unknown_package_is_not_guessed():
    rec = _whisperer().triage_and_suggest_replacements(
        dependency_name="frobnicate", detected_version="2.1", hero_file="pkg/mod.py", hero_code=ARBITRARY_CODE
    )
    assert rec.target_dependency == "frobnicate"
    assert rec.recommended_choice == "manual-review-required"
    assert rec.triage.risk_level == "UNKNOWN"
    assert rec.triage.current_version.value == "2.1"
    assert "toml" not in rec.model_dump_json().lower()


def test_mock_migration_only_rewrites_imports_of_the_given_code():
    patch = _whisperer().synthesize_migration(
        target_file="pkg/mod.py", original_code=ARBITRARY_CODE,
        target_dependency="frobnicate", replacement_library="fribble",
    )
    assert "import fribble as frobnicate" in patch.migrated_code
    assert "def add(a, b=1):" in patch.migrated_code and "class Box:" in patch.migrated_code
    assert "check_site" not in patch.migrated_code


def test_mock_migration_without_source_raises_instead_of_inventing_code():
    with pytest.raises(GemmaBackendError):
        _whisperer().synthesize_migration(
            target_file="pkg/mod.py", original_code="", target_dependency="frobnicate", replacement_library="fribble"
        )


def test_mock_migration_placeholder_replacement_leaves_code_unchanged():
    patch = _whisperer().synthesize_migration(
        target_file="pkg/mod.py", original_code=ARBITRARY_CODE,
        target_dependency="frobnicate", replacement_library="frobnicate-modern",
    )
    assert patch.migrated_code.strip() == ARBITRARY_CODE.strip()


def test_mock_repair_guards_import_with_fallback():
    migrated = _whisperer().synthesize_migration(
        target_file="pkg/mod.py", original_code=ARBITRARY_CODE,
        target_dependency="frobnicate", replacement_library="fribble",
    ).migrated_code
    repair = _whisperer().heal_migration(
        target_file="pkg/mod.py", original_code=ARBITRARY_CODE, current_migrated_code=migrated,
        target_dependency="frobnicate", replacement_library="fribble",
        test_stdout="", test_stderr="Traceback\nModuleNotFoundError: No module named 'fribble'",
    )
    assert repair.success is True
    assert "except ImportError" in repair.repaired_code
    assert "No module named 'fribble'" in repair.root_cause_diagnosis
    compile(repair.repaired_code, "pkg/mod.py", "exec")


def test_mock_generated_suite_is_derived_from_hero_code_and_runs(tmp_path):
    suite = _whisperer().generate_compatibility_suite(
        dependency_name="frobnicate", replacement_library="fribble",
        hero_file="src/mypkg/mod.py", hero_code=ARBITRARY_CODE,
    )
    text = suite.full_pytest_file_content
    assert "'add': ['a', 'b']" in text and "'Box': None" in text
    assert "check_site" not in text

    # Run the Set A gate against a real throwaway repo: it must pass on the unmigrated code.
    pkg = tmp_path / "repo" / "src" / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "mod.py").write_text(ARBITRARY_CODE.replace("import frobnicate\n", "").replace(
        "frobnicate.plus(a, b)", "a + b"))
    test_file = tmp_path / "test_generated.py"
    test_file.write_text(text)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q", "-p", "no:cacheprovider", "-k", "set_a or signatures"],
        cwd=tmp_path, env={**__import__("os").environ, "KAVACH_TARGET_REPO": str(tmp_path / "repo")},
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "3 passed" in proc.stdout