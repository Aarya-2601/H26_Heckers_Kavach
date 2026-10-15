"""
Tests for full DependencyWhisperer pipeline and TeamBridge adapters.
"""

from pathlib import Path
from dependency_whisperer.adapters import TeamBridge
from dependency_whisperer.gemma_client import GemmaClient
from dependency_whisperer.whisperer import DependencyWhisperer


def test_full_pipeline_appdirs():
    client = GemmaClient(backend="mock")
    whisperer = DependencyWhisperer(client=client)
    bridge = TeamBridge(whisperer=whisperer)

    detective_mock = {
        "dependency": "appdirs",
        "version": "1.4.4",
        "hero_file": "LinkWatch/linkwatch/cache.py",
        "usage_locations": [
            {"file": "LinkWatch/linkwatch/cache.py", "line": 4, "snippet": "from appdirs import user_cache_dir"}
        ]
    }
    ingested = bridge.ingest_detective_data(detective_mock)
    assert ingested["dependency_name"] == "appdirs"

    triage_rec = whisperer.triage_and_suggest_replacements(
        dependency_name=ingested["dependency_name"],
        detected_version=ingested["detected_version"],
        usage_locations=ingested["usage_locations"],
        hero_file=ingested["hero_file"],
        hero_code=ingested["hero_code"],
    )
    assert triage_rec.recommended_choice == "platformdirs"
    assert triage_rec.triage.risk_level in ["CRITICAL", "HIGH"]

    chosen_opt = next(o for o in triage_rec.options if o.library_name == triage_rec.recommended_choice)
    tests = whisperer.generate_compatibility_suite(
        dependency_name=ingested["dependency_name"],
        replacement_library=chosen_opt.library_name,
        hero_file=ingested["hero_file"],
        hero_code=ingested["hero_code"],
    )
    assert len(tests.set_a_tests) >= 1

    patch = whisperer.synthesize_migration(
        target_file=ingested["hero_file"],
        original_code=ingested["hero_code"],
        target_dependency=ingested["dependency_name"],
        replacement_library=chosen_opt.library_name,
        api_mappings=chosen_opt.api_mappings,
    )
    assert "platformdirs" in patch.migrated_code

    payload_files = bridge.export_referee_payload(tests, patch, output_dir="referee_sandbox_test")
    assert Path(payload_files["pytest_file"]).exists()

    repair_input = {
        "target_file": ingested["hero_file"],
        "target_dependency": "appdirs",
        "replacement_library": "platformdirs",
        "current_code": patch.migrated_code,
        "test_stdout": "FAILED test_set_a",
        "test_stderr": "TypeError: load requires binary stream",
    }
    repaired = bridge.ingest_referee_failure(repair_input)
    assert repaired.success is True
    assert repaired.root_cause_diagnosis != ""
