"""
Integration Adapters for Person 3 (The AI Whisperer).
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .schemas import (
    DependencyRiskTriage,
    DependencyUsageLocation,
    ExitCapsulePayload,
    MigrationPatch,
    RepairRequest,
    RepairResult,
    ReplacementOption,
    ReplacementRecommendation,
    TestSuitePlan,
)
from .whisperer import DependencyWhisperer


class TeamBridge:
    def __init__(self, whisperer: Optional[DependencyWhisperer] = None):
        self.whisperer = whisperer or DependencyWhisperer()

    def ingest_detective_data(
        self,
        detective_input: Union[Dict[str, Any], str, Path]
    ) -> Dict[str, Any]:
        data = self._load_data(detective_input)

        dep_name = data.get("dependency") or data.get("target_dependency") or data.get("name")
        version = data.get("version") or data.get("current_version") or "unknown"
        hero_file = data.get("hero_file") or data.get("file_path") or ""
        hero_code = data.get("hero_code") or ""

        if not hero_code and hero_file and Path(hero_file).exists():
            hero_code = Path(hero_file).read_text(encoding="utf-8")

        raw_locations = data.get("usage_locations") or data.get("call_sites") or []
        usage_locations = []
        for loc in raw_locations:
            if isinstance(loc, dict):
                usage_locations.append(
                    DependencyUsageLocation(
                        file_path=loc.get("file") or loc.get("file_path") or hero_file or "unknown",
                        line_number=loc.get("line") or loc.get("line_number") or 1,
                        code_snippet=loc.get("snippet") or loc.get("code") or "",
                        call_symbol=loc.get("symbol") or loc.get("call_symbol"),
                    )
                )

        return {
            "dependency_name": dep_name,
            "detected_version": version,
            "hero_file": hero_file,
            "hero_code": hero_code,
            "usage_locations": usage_locations,
        }

    def export_referee_payload(
        self,
        test_suite_plan: TestSuitePlan,
        migration_patch: MigrationPatch,
        output_dir: Union[str, Path] = "referee_sandbox",
    ) -> Dict[str, str]:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        pytest_file = out_path / f"test_{test_suite_plan.target_dependency}_migration.py"
        pytest_file.write_text(test_suite_plan.full_pytest_file_content, encoding="utf-8")

        target_name = Path(migration_patch.target_file).name or "migrated_file.py"
        migrated_file = out_path / target_name
        migrated_file.write_text(migration_patch.migrated_code, encoding="utf-8")

        diff_file = out_path / f"{test_suite_plan.target_dependency}_migration.patch"
        diff_file.write_text(migration_patch.unified_diff, encoding="utf-8")

        return {
            "pytest_file": str(pytest_file),
            "migrated_file": str(migrated_file),
            "diff_file": str(diff_file),
            "target_dependency": test_suite_plan.target_dependency,
            "replacement_library": test_suite_plan.replacement_library,
        }

    def ingest_referee_failure(
        self,
        referee_failure_input: Union[Dict[str, Any], str, Path]
    ) -> RepairResult:
        data = self._load_data(referee_failure_input)

        target_file = data.get("target_file", "unknown.py")
        original_code = data.get("original_code", "")
        current_code = data.get("current_migrated_code") or data.get("current_code", "")
        dep_name = data.get("target_dependency", "")
        replacement = data.get("replacement_library", "")
        test_stdout = data.get("test_stdout") or data.get("stdout") or ""
        test_stderr = data.get("test_stderr") or data.get("stderr") or data.get("traceback") or ""

        return self.whisperer.heal_migration(
            target_file=target_file,
            original_code=original_code,
            current_migrated_code=current_code,
            target_dependency=dep_name,
            replacement_library=replacement,
            test_stdout=test_stdout,
            test_stderr=test_stderr,
            attempt_number=data.get("attempt_number", 1),
        )

    def export_presenter_capsule(
        self,
        exit_capsule_payload: ExitCapsulePayload,
        output_json_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        capsule_dict = exit_capsule_payload.model_dump()
        if output_json_path:
            p = Path(output_json_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(capsule_dict, indent=2), encoding="utf-8")
        return capsule_dict

    def _load_data(self, input_val: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        if isinstance(input_val, dict):
            return input_val
        if isinstance(input_val, (str, Path)):
            p = Path(input_val)
            if p.exists() and p.is_file():
                return json.loads(p.read_text(encoding="utf-8"))
            try:
                return json.loads(str(input_val))
            except Exception:
                return {"raw_text": str(input_val)}
        return {}
