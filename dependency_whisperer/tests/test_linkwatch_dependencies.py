"""
Tests for LinkWatch Real-World Dependencies (toml, appdirs).
"""

from pathlib import Path
from dependency_whisperer.gemma_client import GemmaClient
from dependency_whisperer.whisperer import DependencyWhisperer


def test_toml_to_tomllib_migration():
    whisperer = DependencyWhisperer(client=GemmaClient(backend="mock"))
    config_file = "LinkWatch/linkwatch/config.py"
    config_code = Path(config_file).read_text(encoding="utf-8") if Path(config_file).exists() else "import toml"

    triage = whisperer.triage_and_suggest_replacements(
        dependency_name="toml",
        detected_version="0.10.2",
        hero_file=config_file,
        hero_code=config_code,
    )
    assert triage.recommended_choice == "tomllib"

    patch = whisperer.synthesize_migration(
        target_file=config_file,
        original_code=config_code,
        target_dependency="toml",
        replacement_library="tomllib",
    )
    assert "tomllib" in patch.migrated_code


def test_appdirs_to_platformdirs_migration():
    whisperer = DependencyWhisperer(client=GemmaClient(backend="mock"))
    cache_file = "LinkWatch/linkwatch/cache.py"
    cache_code = Path(cache_file).read_text(encoding="utf-8") if Path(cache_file).exists() else "from appdirs import user_cache_dir"

    triage = whisperer.triage_and_suggest_replacements(
        dependency_name="appdirs",
        detected_version="1.4.4",
        hero_file=cache_file,
        hero_code=cache_code,
    )
    assert triage.recommended_choice == "platformdirs"

    patch = whisperer.synthesize_migration(
        target_file=cache_file,
        original_code=cache_code,
        target_dependency="appdirs",
        replacement_library="platformdirs",
    )
    assert "platformdirs" in patch.migrated_code
