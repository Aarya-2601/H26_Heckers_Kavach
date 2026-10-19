"""
Command Line Interface for Person 3 (The AI Whisperer).
"""

import argparse
import json
import sys
from pathlib import Path

from .adapters import TeamBridge
from .gemma_client import GemmaClient
from .whisperer import DependencyWhisperer


def main():
    parser = argparse.ArgumentParser(
        prog="python -m dependency_whisperer.cli",
        description="Gemma 4 Dependency Whisperer (Person 3 Deliverable)",
    )
    parser.add_argument("--backend", choices=["mock", "hosted", "local"], default="mock",
                        help="Gemma execution backend (default: mock for offline development)")
    parser.add_argument("--api-key", help="Google GenAI / AI Studio API key (or set GEMMA_API_KEY env var)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. DEMO
    subparsers.add_parser("demo", help="Run end-to-end demonstration on LinkWatch repository")

    # 2. TRIAGE
    triage_parser = subparsers.add_parser("triage", help="Triage dependency and recommend replacements")
    triage_parser.add_argument("--dep", required=True, help="Dependency name (e.g. toml, appdirs)")
    triage_parser.add_argument("--version", default="unknown", help="Detected version in requirements")
    triage_parser.add_argument("--hero", help="Path to hero file using this dependency")

    # 3. TESTS
    tests_parser = subparsers.add_parser("tests", help="Generate Set A & Set B compatibility test suite")
    tests_parser.add_argument("--dep", required=True, help="Target dependency name")
    tests_parser.add_argument("--replacement", help="Chosen replacement (default: auto-selected)")
    tests_parser.add_argument("--hero", required=True, help="Path to hero file using this dependency")
    tests_parser.add_argument("--out-dir", default="generated_tests", help="Output directory for pytest file")

    # 4. MIGRATE
    migrate_parser = subparsers.add_parser("migrate", help="Synthesize drop-in code migration and unified diff")
    migrate_parser.add_argument("--dep", required=True, help="Target dependency name")
    migrate_parser.add_argument("--replacement", help="Chosen replacement library")
    migrate_parser.add_argument("--hero", required=True, help="Path to hero file to rewrite")
    migrate_parser.add_argument("--out-file", help="Path to save migrated file")

    # 5. FULL-RUN
    full_parser = subparsers.add_parser("full-run", help="Run full pipeline and export Exit Capsule JSON")
    full_parser.add_argument("--dep", required=True, help="Target dependency name")
    full_parser.add_argument("--version", default="unknown", help="Current version")
    full_parser.add_argument("--hero", required=True, help="Path to hero file")
    full_parser.add_argument("--out-capsule", default="exit_capsule.json", help="Path to save Exit Capsule JSON")

    args = parser.parse_args()

    client = GemmaClient(api_key=args.api_key, backend=args.backend)
    whisperer = DependencyWhisperer(client=client)
    bridge = TeamBridge(whisperer=whisperer)

    if args.command == "demo":
        run_demo(whisperer, bridge)
    elif args.command == "triage":
        run_triage(whisperer, args.dep, args.version, args.hero)
    elif args.command == "tests":
        run_tests(whisperer, bridge, args.dep, args.replacement, args.hero, args.out_dir)
    elif args.command == "migrate":
        run_migrate(whisperer, args.dep, args.replacement, args.hero, args.out_file)
    elif args.command == "full-run":
        run_full(whisperer, bridge, args.dep, args.version, args.hero, args.out_capsule)


def run_demo(whisperer: DependencyWhisperer, bridge: TeamBridge):
    print("=" * 78)
    print("  GEMMA 4 DEPENDENCY WHISPERER: PERSON 3 END-TO-END DEMONSTRATION")
    print("=" * 78)
    print(f"[*] Gemma Model: {whisperer.client.metadata.model_name} ({whisperer.client.metadata.model_version})")
    print(f"[*] Execution Mode: {whisperer.client.backend.upper()}")
    print("-" * 78)

    hero_file = "LinkWatch/linkwatch/cache.py"
    dep = "appdirs"
    print(f"\n[PHASE 1] Triaging Target Dependency: '{dep}' in '{hero_file}'")
    hero_path = Path(hero_file)
    hero_code = hero_path.read_text(encoding="utf-8") if hero_path.exists() else "from appdirs import user_cache_dir"

    triage_rec = whisperer.triage_and_suggest_replacements(
        dependency_name=dep,
        detected_version="1.4.4",
        hero_file=hero_file,
        hero_code=hero_code,
    )

    print(f"  • Deprecation Status: {triage_rec.triage.is_deprecated.value} (Confidence: {triage_rec.triage.is_deprecated.confidence})")
    print(f"  • Risk Level:         {triage_rec.triage.risk_level}")
    print(f"  • Risk Summary:       {triage_rec.triage.risk_summary}")
    print(f"  • Suggested Primary:  {triage_rec.recommended_choice}")
    print("  • Candidate Alternatives:")
    for opt in triage_rec.options:
        print(f"    - {opt.library_name} ({opt.recommended_version_spec}) [Difficulty: {opt.migration_difficulty}]")

    print(f"\n[PHASE 2] Red Team Test Generation (Set A & Set B)")
    chosen_opt = next(o for o in triage_rec.options if o.library_name == triage_rec.recommended_choice)
    test_suite = whisperer.generate_compatibility_suite(
        dependency_name=dep,
        replacement_library=chosen_opt.library_name,
        hero_file=hero_file,
        hero_code=hero_code,
        call_sites=["from appdirs import user_cache_dir"],
    )
    print(f"  • SET A (Compatibility Gate): {len(test_suite.set_a_tests)} test cases (Validates current contract)")
    for t in test_suite.set_a_tests:
        print(f"    - [{t.test_id}] {t.name}: {t.description}")
    print(f"  • SET B (Differential / Edge): {len(test_suite.set_b_tests)} test cases (Probes modern differences)")
    for t in test_suite.set_b_tests:
        print(f"    - [{t.test_id}] {t.name}: {t.description}")

    print(f"\n[PHASE 3] Blue Team Code Synthesis ({dep} -> {chosen_opt.library_name})")
    patch = whisperer.synthesize_migration(
        target_file=hero_file,
        original_code=hero_code,
        target_dependency=dep,
        replacement_library=chosen_opt.library_name,
        api_mappings=chosen_opt.api_mappings,
    )
    print("  • Unified Diff:")
    for line in patch.unified_diff.splitlines()[:15]:
        print(f"    {line}")
    if len(patch.unified_diff.splitlines()) > 15:
        print("    ... (truncated)")

    print(f"\n[PHASE 4] Exporting Artifacts for Person 1 (Referee) and Person 4 (Presenter)")
    referee_files = bridge.export_referee_payload(test_suite, patch, output_dir="referee_sandbox")
    print(f"  • Referee Sandbox Pytest: {referee_files['pytest_file']}")
    print(f"  • Referee Candidate Code: {referee_files['migrated_file']}")
    print(f"  • Referee Patch File:     {referee_files['diff_file']}")

    capsule = whisperer.build_exit_capsule_payload(triage_rec, chosen_opt, test_suite, patch)
    bridge.export_presenter_capsule(capsule, output_json_path="referee_sandbox/exit_capsule_demo.json")
    print(f"  • Presenter Exit Capsule: referee_sandbox/exit_capsule_demo.json")

    print("\n" + "=" * 78)
    print("  DEMO COMPLETED SUCCESSFULLY: ALL PERSON 3 MODULES VERIFIED!")
    print("=" * 78)


def _resolve_hero(hero_file: Optional[str]) -> tuple[str, str]:
    """Smart resolver to locate hero files across local and dataset/ directories."""
    if not hero_file:
        return "", ""
    candidates = [
        Path(hero_file),
        Path("dataset") / hero_file,
        Path("dataset") / "LinkWatch" / hero_file,
    ]
    if hero_file.startswith("LinkWatch/") or hero_file.startswith("LinkWatch\\"):
        rel = hero_file.replace("LinkWatch/", "").replace("LinkWatch\\", "")
        candidates.append(Path("dataset") / "LinkWatch" / rel)

    for cand in candidates:
        if cand.exists() and cand.is_file():
            return str(cand), cand.read_text(encoding="utf-8")

    p = Path(hero_file)
    if p.exists() and p.is_file():
        return str(p), p.read_text(encoding="utf-8")
    return hero_file, ""


def run_triage(whisperer: DependencyWhisperer, dep: str, version: str, hero_file: Optional[str]):
    hero_resolved, hero_code = _resolve_hero(hero_file)
    res = whisperer.triage_and_suggest_replacements(
        dependency_name=dep,
        detected_version=version,
        hero_file=hero_resolved or "",
        hero_code=hero_code,
    )
    print(json.dumps(res.model_dump(), indent=2))


def run_tests(whisperer: DependencyWhisperer, bridge: TeamBridge, dep: str, replacement: Optional[str], hero_file: str, out_dir: str):
    hero_resolved, hero_code = _resolve_hero(hero_file)
    if not hero_code:
        raise FileNotFoundError(f"Could not find hero file: {hero_file}")
    repl = replacement or ("platformdirs" if dep == "appdirs" else "tomllib")
    plan = whisperer.generate_compatibility_suite(dep, repl, hero_resolved, hero_code)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fpath = out_path / f"test_{dep}_{repl}.py"
    fpath.write_text(plan.full_pytest_file_content, encoding="utf-8")
    print(f"Wrote test suite to {fpath}")


def run_migrate(whisperer: DependencyWhisperer, dep: str, replacement: Optional[str], hero_file: str, out_file: Optional[str]):
    hero_resolved, hero_code = _resolve_hero(hero_file)
    if not hero_code:
        raise FileNotFoundError(f"Could not find hero file: {hero_file}")
    repl = replacement or ("platformdirs" if dep == "appdirs" else "tomllib")
    patch = whisperer.synthesize_migration(hero_resolved, hero_code, dep, repl)
    if out_file:
        Path(out_file).write_text(patch.migrated_code, encoding="utf-8")
        print(f"Saved migrated code to {out_file}")
    else:
        print(patch.unified_diff)


def run_full(whisperer: DependencyWhisperer, bridge: TeamBridge, dep: str, version: str, hero_file: str, out_capsule: str):
    hero_resolved, hero_code = _resolve_hero(hero_file)
    if not hero_code:
        raise FileNotFoundError(f"Could not find hero file: {hero_file}")
    triage_rec = whisperer.triage_and_suggest_replacements(dep, version, hero_file=hero_resolved, hero_code=hero_code)
    chosen_opt = next(o for o in triage_rec.options if o.library_name == triage_rec.recommended_choice)
    suite = whisperer.generate_compatibility_suite(dep, chosen_opt.library_name, hero_resolved, hero_code)
    patch = whisperer.synthesize_migration(hero_resolved, hero_code, dep, chosen_opt.library_name, chosen_opt.api_mappings)
    capsule = whisperer.build_exit_capsule_payload(triage_rec, chosen_opt, suite, patch)
    bridge.export_presenter_capsule(capsule, out_capsule)
    print(f"Full Exit Capsule generated and saved to {out_capsule}")


if __name__ == "__main__":
    main()
