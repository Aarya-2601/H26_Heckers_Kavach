"""
Tests for real-world dependency migrations (toml -> tomllib, appdirs -> platformdirs).
Uses small inline sample modules so the tests do not depend on any particular repository.
"""

from dependency_whisperer.gemma_client import GemmaClient
from dependency_whisperer.whisperer import DependencyWhisperer

SAMPLE_CONFIG_FILE = "sample_app/config.py"
SAMPLE_CONFIG_CODE = "import toml\n\n\ndef load_settings(path):\n    return toml.load(path)\n"

SAMPLE_CACHE_FILE = "sample_app/cache.py"
SAMPLE_CACHE_CODE = (
    "import os\n"
    "from appdirs import user_cache_dir\n\n\n"
    "def cache_dir():\n"
    "    path = user_cache_dir(\"sample_app\")\n"
    "    os.makedirs(path, exist_ok=True)\n"
    "    return path\n"
)


def test_toml_to_tomllib_migration():
    whisperer = DependencyWhisperer(client=GemmaClient(backend="mock"))

    triage = whisperer.triage_and_suggest_replacements(
        dependency_name="toml",
        detected_version="0.10.2",
        hero_file=SAMPLE_CONFIG_FILE,
        hero_code=SAMPLE_CONFIG_CODE,
    )
    assert triage.recommended_choice == "tomllib"

    patch = whisperer.synthesize_migration(
        target_file=SAMPLE_CONFIG_FILE,
        original_code=SAMPLE_CONFIG_CODE,
        target_dependency="toml",
        replacement_library="tomllib",
    )
    assert "tomllib" in patch.migrated_code


def test_appdirs_to_platformdirs_migration():
    whisperer = DependencyWhisperer(client=GemmaClient(backend="mock"))

    triage = whisperer.triage_and_suggest_replacements(
        dependency_name="appdirs",
        detected_version="1.4.4",
        hero_file=SAMPLE_CACHE_FILE,
        hero_code=SAMPLE_CACHE_CODE,
    )
    assert triage.recommended_choice == "platformdirs"

    patch = whisperer.synthesize_migration(
        target_file=SAMPLE_CACHE_FILE,
        original_code=SAMPLE_CACHE_CODE,
        target_dependency="appdirs",
        replacement_library="platformdirs",
    )
    assert "platformdirs" in patch.migrated_code