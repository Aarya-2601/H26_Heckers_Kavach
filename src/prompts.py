"""Interactive Terminal Prompts module using questionary.

Implements selection menus and text prompts styled in peachy-orange (#ffaf87).
Supports optional dynamic voice capture and text editing.
"""

from typing import Any, Dict, List, Optional
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


def prompt_select_dependency(
    choices: Optional[List[str]] = None,
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt the user to select a dependency to replace (styled in peachy-orange)."""
    options = choices or DEFAULT_DEPENDENCY_CHOICES
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
