"""Theme and Rich Console configuration for the CLI.

Defines the custom color palette and console instance:
- AI outputs: light blue (bright_cyan)
- Human inputs/actions: peachy-orange (rgb(255,175,135))
- Flagged files/elements: bold red
- Neutral elements: neutral gray or white
"""

import sys
from rich.console import Console
from rich.theme import Theme

# Ensure UTF-8 output encoding across platforms (notably Windows legacy console)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Color palette definition
COLOR_AI_OUTPUT = "bright_cyan"
COLOR_HUMAN_ACTION = "rgb(255,175,135)"
COLOR_FLAGGED = "bold red"
COLOR_NEUTRAL_WHITE = "white"
COLOR_NEUTRAL_GRAY = "bright_black"
COLOR_DIM = "dim white"

# Custom Rich Theme mapping semantic roles to the specified color palette
custom_theme = Theme(
    {
        # AI outputs mapped to light blue (bright_cyan)
        "ai": COLOR_AI_OUTPUT,
        "ai_output": COLOR_AI_OUTPUT,
        "ai.text": COLOR_AI_OUTPUT,
        # Human inputs/actions mapped to peachy-orange (rgb(255,175,135))
        "human": COLOR_HUMAN_ACTION,
        "human_action": COLOR_HUMAN_ACTION,
        "human.input": COLOR_HUMAN_ACTION,
        # Flagged / Alert styles
        "flagged": COLOR_FLAGGED,
        "alert": COLOR_FLAGGED,
        # Neutral styling for directory tree & structural elements
        "tree.root": "bold white",
        "tree.dir": COLOR_NEUTRAL_WHITE,
        "tree.file": COLOR_DIM,
        "tree.file.flagged": COLOR_FLAGGED,
        "neutral": COLOR_NEUTRAL_GRAY,
        "neutral.white": COLOR_NEUTRAL_WHITE,
        "neutral.gray": COLOR_NEUTRAL_GRAY,
    }
)

# Shared Rich Console instance initialized with the custom palette
console = Console(theme=custom_theme)


def print_ai(message: str, **kwargs) -> None:
    """Print an AI output message in light blue (bright_cyan)."""
    console.print(f"[ai]{message}[/ai]", **kwargs)


def print_human(message: str, **kwargs) -> None:
    """Print a Human input or action message in peachy-orange (rgb(255,175,135))."""
    console.print(f"[human]{message}[/human]", **kwargs)
