"""Interactive Terminal Prompts module using questionary.

Implements selection menus and text prompts styled in peachy-orange (#ffaf87).
Supports optional dynamic voice capture and text editing.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import questionary
from questionary import Choice, Style

from src.theme import console, print_human, print_solution
from src.voice import capture_voice_input

# Peachy-orange palette hex code matching rgb(255, 175, 135)
PEACHY_ORANGE_HEX = "#ffaf87"

# Custom Questionary style with prompt text in peachy-orange
custom_questionary_style = Style(
    [
        ("qmark", f"fg:{PEACHY_ORANGE_HEX} bold"),
        ("question", f"fg:{PEACHY_ORANGE_HEX} bold"),
        ("answer", f"fg:{PEACHY_ORANGE_HEX} bold"),
        ("pointer", f"fg:{PEACHY_ORANGE_HEX} bold"),
        ("highlighted", f"fg:{PEACHY_ORANGE_HEX} bold"),
        ("selected", f"fg:{PEACHY_ORANGE_HEX}"),
        ("separator", "fg:#767676"),
        ("instruction", "fg:#767676 italic"),
        ("text", f"fg:{PEACHY_ORANGE_HEX}"),
        ("disabled", "fg:#555555 italic"),
    ]
)

# Default LinkWatch dependencies for replacement/audit menu
DEFAULT_DEPENDENCY_CHOICES: List[str] = [
    "requests (vulnerable to global monkey-patch in http_patch.py -> replace with httpx)",
    "certifi (root certificates validation in checker.py)",
    "jinja2 (HTML status template renderer in report.py)",
    "appdirs (legacy cache path provider in cache.py -> replace with platformdirs)",
    "Skip dependency replacement",
]

# Default LinkWatch flagged files for remediation menu
DEFAULT_FLAGGED_CHOICES: List[str] = [
    "linkwatch/http_patch.py (Global Session monkey-patching)",
    "linkwatch/checker.py (Missing HTTP request timeout)",
    "Dockerfile (Missing non-root USER instruction)",
    "sites.toml (User configuration validation)",
]

# Input mode options making voice input optional
INPUT_METHOD_CHOICES: List[str] = [
    "Voice Input (Speak into mic; recording concludes 5s after you stop speaking)",
    "Manual Input (Type remediation instruction directly)",
]


def detect_repo_dependency_choices(repo_path: Optional[Union[str, Path]] = None) -> List[str]:
    """Dynamically scan repository dependencies from manifests and AST for the selection menu."""
    if not repo_path or not os.path.exists(str(repo_path)):
        return list(DEFAULT_DEPENDENCY_CHOICES)

    repo = Path(repo_path)
    choices: List[str] = []
    seen = set()
    migrated_records: Dict[str, Dict[str, Any]] = {}
    history_file = repo / ".kavach_migrations.json"
    if history_file.exists():
        try:
            hdata = json.loads(history_file.read_text(encoding="utf-8"))
            for m in hdata.get("migrations", []):
                tp = m.get("target_package")
                if tp:
                    migrated_records[tp.lower()] = m
        except Exception:
            pass

    # 1. First show previously migrated packages so user clearly sees them as fixed
    for tp_lower, m in migrated_records.items():
        tp_name = m.get("target_package", tp_lower)
        rep_name = m.get("replacement_package", "modernized")
        seen.add(tp_lower)
        choices.append(f"[ALREADY MIGRATED ✓] {tp_name} (resolved on disk -> replaced with {rep_name})")

    # 2. Dynamic AST & Manifest analysis
    try:
        from web import analysis as kv_analysis
        analysis = kv_analysis.analyze_repo(repo)
        candidates = analysis.get("candidates", [])
        for c in candidates:
            pkg = c.get("package")
            if not pkg or pkg.lower() in seen:
                continue
            seen.add(pkg.lower())
            repl = c.get("suggested_replacement")
            reason = c.get("reason")
            call_count = c.get("call_sites", 0)

            if repl and reason:
                choices.append(f"{pkg} ({reason} -> replace with {repl})")
            elif repl:
                choices.append(f"{pkg} (detected -> replace with {repl})")
            elif call_count > 0:
                choices.append(f"{pkg} (found in {call_count} AST call site(s))")
            else:
                choices.append(f"{pkg} (declared in manifest)")

        manifest = analysis.get("manifest", {})
        for name in manifest.keys():
            if name.lower() not in seen:
                seen.add(name.lower())
                choices.append(f"{name} (declared in manifest)")
    except Exception:
        pass

    # 3. If repo has no manifests or known candidates, scan python files directly
    unresolved_count = len([c for c in choices if not c.startswith("[ALREADY MIGRATED")])
    if unresolved_count == 0:
        try:
            import ast
            counts: Dict[str, int] = {}
            for p in repo.rglob("*.py"):
                if any(part in p.parts for part in (".git", "venv", ".venv", "__pycache__", ".pytest_cache", "build", "dist")):
                    continue
                try:
                    tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for n in node.names:
                                top = n.name.split(".")[0]
                                counts[top] = counts.get(top, 0) + 1
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            top = node.module.split(".")[0]
                            counts[top] = counts.get(top, 0) + 1
                except Exception:
                    pass

            from web.analysis import KNOWN_REPLACEMENTS
            for mod_name, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
                if mod_name.lower() in seen:
                    continue
                seen.add(mod_name.lower())
                repl_info = KNOWN_REPLACEMENTS.get(mod_name.lower())
                if repl_info:
                    choices.append(f"{mod_name} ({repl_info[1]} -> replace with {repl_info[0]})")
                else:
                    choices.append(f"{mod_name} (imported in {cnt} file(s))")
        except Exception:
            pass

    if not choices:
        return list(DEFAULT_DEPENDENCY_CHOICES)

    choices.append("Skip dependency replacement")
    return choices


def prompt_select_dependency(
    choices: Optional[List[str]] = None,
    repo_path: Optional[Union[str, Path]] = None,
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt the user to select a dependency to replace (styled in peachy-orange)."""
    if choices:
        options = choices
    elif repo_path:
        options = detect_repo_dependency_choices(repo_path)
    else:
        options = DEFAULT_DEPENDENCY_CHOICES
    target_style = style or custom_questionary_style

    answer = questionary.select(
        "Select the dependency to replace:",
        choices=options,
        style=target_style,
        qmark="▶",
    ).ask()
    return answer


def prompt_select_flagged_file(
    choices: Optional[List[str]] = None,
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt the user to select a flagged file for AST remediation."""
    options = choices or DEFAULT_FLAGGED_CHOICES
    target_style = style or custom_questionary_style

    answer = questionary.select(
        "Select the flagged file to remediate:",
        choices=options,
        style=target_style,
        qmark="▶",
    ).ask()
    return answer


def prompt_select_input_method(
    choices: Optional[List[str]] = None,
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt user to choose between optional voice input or manual typing."""
    options = choices or INPUT_METHOD_CHOICES
    target_style = style or custom_questionary_style

    answer = questionary.select(
        "Choose remediation input method:",
        choices=options,
        style=target_style,
        qmark="▶",
    ).ask()
    return answer


def prompt_remediation_input(
    default_text: str = "",
    message: str = "Edit or confirm remediation instruction (Press Enter to submit):",
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt the user for remediation input, pre-populated with voice transcription for editing."""
    target_style = style or custom_questionary_style

    answer = questionary.text(
        message,
        default=default_text,
        style=target_style,
        qmark="▶",
    ).ask()
    return answer


def run_interactive_workflow(
    listen_voice: Optional[bool] = None,
    mock_voice_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Orchestrate the full interactive flow for Phase 2.

    1. Prompt user to select dependency to replace (styled in peachy-orange).
    2. Prompt user to select flagged file for remediation.
    3. Optionally choose voice input or manual typing.
    4. If voice: records while speaking and waits 5s after silence, then populates prompt for editing.
    5. Displays the bold solution separated by one line space.
    """
    console.print()
    console.print("[dim white]─── [Phase 2] Interactive Selection & Optional Voice Capture ───[/dim white]")

    # Step 2.1: Terminal Selection Menu
    selected_dep = prompt_select_dependency()
    if not selected_dep:
        selected_dep = DEFAULT_DEPENDENCY_CHOICES[0]
    print_human(f"Selected Dependency: {selected_dep}")

    selected_file = prompt_select_flagged_file()
    if not selected_file:
        selected_file = DEFAULT_FLAGGED_CHOICES[0]
    print_human(f"Selected File Target: {selected_file}")

    console.print()

    # Determine whether to use voice input (optional)
    use_voice = listen_voice
    if use_voice is None and mock_voice_text is None:
        chosen_method = prompt_select_input_method()
        use_voice = bool(chosen_method and "Voice" in chosen_method)
    elif mock_voice_text is not None:
        use_voice = True

    voice_text = ""
    if use_voice:
        console.print("[dim white]─── Dynamic Voice Input Capture ───[/dim white]")
        voice_text = capture_voice_input(
            silence_after_speech=5.0,
            fallback_text="replace requests with httpx in linkwatch/checker.py",
            mock_input=mock_voice_text,
        )

    # Questionary prompt with populated voice input for editing
    console.print()
    console.print("[dim white]─── Terminal Prompt (Editable Input) ───[/dim white]")
    final_action = prompt_remediation_input(default_text=voice_text)
    if not final_action:
        final_action = voice_text or "replace requests with httpx in linkwatch/checker.py"

    print_human(f"Confirmed Remediation Action: {final_action}")

    # One line space between question and solution
    console.print()

    # Solution text made bold without AI emoji
    print_solution(
        f"Scheduled remediation AST rewrite for '{selected_file}' with action: '{final_action}'."
    )

    return {
        "dependency": selected_dep,
        "file": selected_file,
        "voice_transcription": voice_text,
        "final_action": final_action,
    }
