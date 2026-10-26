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


# Fallback dependency menu when no repository can be inspected: custom entry only
DEFAULT_DEPENDENCY_CHOICES: List[str] = [
    "[Enter custom dependency name]",
]

# Fallback file menu when no repository can be inspected: custom entry only
DEFAULT_FLAGGED_CHOICES: List[str] = [
    "[Enter custom file path]",
]

# Input mode options making voice input optional
INPUT_METHOD_CHOICES: List[str] = [
    "Voice Input (Speak into mic; recording concludes 5s after you stop speaking)",
    "Manual Input (Type remediation instruction directly)",
]

STDLIB_MODULES = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii", "bisect", "builtins",
    "bz2", "calendar", "cmath", "cmd", "code", "codecs", "collections", "colorsys", "compileall",
    "concurrent", "configparser", "contextlib", "contextvars", "copy", "copyreg", "cProfile", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis", "distutils",
    "doctest", "email", "encodings", "ensurepip", "enum", "errno", "faulthandler", "fcntl", "filecmp",
    "fileinput", "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
    "glob", "graphlib", "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib",
    "imghdr", "importlib", "inspect", "io", "ipaddress", "itertools", "json", "keyword", "lib2to3",
    "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "msilib", "msvcrt", "multiprocessing", "netrc", "nntplib", "numbers",
    "operator", "optparse", "os", "ossaudiodev", "pathlib", "pdb", "pickle", "pickletools", "pipes",
    "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats",
    "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random", "re", "readline",
    "reprlib", "resource", "rlcompleter", "runpy", "sched", "secrets", "select", "selectors", "shelve",
    "shlex", "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "spwd", "sqlite3", "ssl", "stat", "statistics", "string", "stringprep", "struct", "subprocess",
    "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile",
    "termios", "test", "textwrap", "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib"
}


def detect_repo_dependencies(repo_path: str) -> List[str]:
    """Scan manifests and Python AST imports in any target repository."""
    import ast
    import re
    from pathlib import Path
    deps = set()
    rpath = Path(repo_path)
    if not rpath.exists():
        return list(DEFAULT_DEPENDENCY_CHOICES)

    # 1. Parse requirements*.txt
    for req_file in rpath.glob("requirements*.txt"):
        try:
            for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    pkg = re.split(r"[><=~!]", line)[0].strip()
                    if pkg and not pkg.startswith("."):
                        deps.add(pkg.lower())
        except Exception:
            pass

    # 2. Parse pyproject.toml
    pyproject = rpath / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'["\']([a-zA-Z0-9_\-]+)(?:[><=~!]|\s*["\'])', text):
                candidate = m.group(1).lower()
                if candidate not in {"project", "tool", "build-system", "version", "name", "description"}:
                    deps.add(candidate)
        except Exception:
            pass

    # 3. Parse setup.py / setup.cfg
    for setup_file in [rpath / "setup.py", rpath / "setup.cfg"]:
        if setup_file.exists():
            try:
                text = setup_file.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r'["\']([a-zA-Z0-9_\-]+)(?:[><=~!]|\s*["\'])', text):
                    candidate = m.group(1).lower()
                    if len(candidate) > 2 and candidate not in {"setup", "find_packages", "version", "description", "author"}:
                        deps.add(candidate)
            except Exception:
                pass

    # 4. AST Scan Python files
    local_modules = {p.stem.lower() for p in rpath.rglob("*.py")}
    skip_dirs = {".git", "venv", ".venv", "env", "node_modules", "__pycache__", "build", "dist"}
    for py_file in rpath.rglob("*.py"):
        if any(part in skip_dirs for part in py_file.parts):
            continue
        try:
            src = py_file.read_text(encoding="utf-8-sig", errors="ignore")
            tree = ast.parse(src, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0].lower()
                        if top not in STDLIB_MODULES and top not in local_modules and len(top) > 1:
                            deps.add(top)
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        top = node.module.split(".")[0].lower()
                        if top not in STDLIB_MODULES and top not in local_modules and len(top) > 1:
                            deps.add(top)
        except Exception:
            continue

    if not deps:
        return list(DEFAULT_DEPENDENCY_CHOICES)

    return sorted(list(deps)) + ["[Enter custom dependency name]"]


def detect_repo_files(repo_path: str, max_files: int = 15) -> List[str]:
    """Find relevant Python files in any target repository."""
    from pathlib import Path
    rpath = Path(repo_path)
    if not rpath.exists():
        return list(DEFAULT_FLAGGED_CHOICES)

    files = []
    skip_dirs = {".git", "venv", ".venv", "env", "node_modules", "__pycache__", "build", "dist"}
    for py_file in rpath.rglob("*.py"):
        if any(part in skip_dirs for part in py_file.parts):
            continue
        rel = str(py_file.relative_to(rpath)).replace("\\", "/")
        files.append(rel)
        if len(files) >= max_files:
            break

    # Add Dockerfile or config files if present
    for extra in ["Dockerfile", "pyproject.toml", "requirements.txt"]:
        if (rpath / extra).exists() and extra not in files:
            files.append(extra)

    if not files:
        return list(DEFAULT_FLAGGED_CHOICES)

    return sorted(files) + ["[Enter custom file path]"]


def prompt_select_dependency(
    choices: Optional[List[str]] = None,
    repo_path: Optional[str] = None,
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt the user to select a dependency to replace (styled in peachy-orange)."""
    if choices is None and repo_path:
        options = detect_repo_dependencies(repo_path)
    else:
        options = choices or DEFAULT_DEPENDENCY_CHOICES
    target_style = style or custom_questionary_style

    answer = questionary.select(
        "Select the dependency to replace:",
        choices=options,
        style=target_style,
        qmark="▶",
    ).ask()

    if answer == "[Enter custom dependency name]":
        custom = questionary.text(
            "Enter target dependency package name:",
            style=target_style,
            qmark="▶",
        ).ask()
        return (custom or "").strip()

    return answer


def prompt_select_flagged_file(
    choices: Optional[List[str]] = None,
    repo_path: Optional[str] = None,
    style: Optional[Style] = None,
) -> Optional[str]:
    """Prompt the user to select a flagged file for AST remediation."""
    if choices is None and repo_path:
        options = detect_repo_files(repo_path)
    else:
        options = choices or DEFAULT_FLAGGED_CHOICES
    target_style = style or custom_questionary_style

    answer = questionary.select(
        "Select the flagged file to remediate:",
        choices=options,
        style=target_style,
        qmark="▶",
    ).ask()

    if answer == "[Enter custom file path]":
        custom = questionary.text(
            "Enter relative file path to remediate:",
            style=target_style,
            qmark="▶",
        ).ask()
        return (custom or "").strip()

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
    repo_path: Optional[str] = None,
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
    selected_dep = prompt_select_dependency(repo_path=repo_path)
    if not selected_dep:
        raise SystemExit("No dependency selected.")
    print_human(f"Selected Dependency: {selected_dep}")

    selected_file = prompt_select_flagged_file(repo_path=repo_path)
    if not selected_file:
        raise SystemExit("No file selected.")
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
            mock_input=mock_voice_text,
        )

    # Questionary prompt with populated voice input for editing
    console.print()
    console.print("[dim white]─── Terminal Prompt (Editable Input) ───[/dim white]")
    final_action = prompt_remediation_input(default_text=voice_text)
    if not final_action:
        final_action = voice_text
    if not final_action:
        raise SystemExit("No remediation instruction provided.")

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