"""
Scoped anti-tamper checks used by the sandbox and the reward function.

Self-contained on purpose: these run even when analyzer/ (Person 2's auditor) is unavailable.
A test file is recognised by its path *components*, never by a substring, so `pytest/`,
`latest/` or `contest.py` are ordinary source files. Assertions only matter inside test files:
deleting an `assert` from library code is a legitimate edit.

tests/test_tamper_scope.py asserts that is_test_path agrees with analyzer.auditor.is_test_path.
"""

import re
from typing import Dict, List

TEST_DIRS = {"test", "tests", ".locked_tests", ".audit_tests"}
TEST_CONFIG_FILES = {"conftest.py", "pytest.ini"}

_ASSERT_RE = re.compile(r"^\s*(?:with\s+)?(?:assert\b|(?:[\w.]+\.)?assert\w*\(|pytest\.raises\b)")
_COMMENTED_ASSERT_RE = re.compile(r"^\s*#\s*(assert\b|self\.assert\w*\()")
_SKIP_RE = re.compile(
    r"\bmark\.(skip|skipif|xfail)\b|pytest\.(skip|xfail|importorskip)\(|unittest\.(skip\w*|expectedFailure)|\bSkipTest\b"
)


def is_test_path(path: str) -> bool:
    parts = path.replace("\\", "/").lower().split("/")
    name = parts[-1]
    return (
        any(part in TEST_DIRS for part in parts[:-1])
        or name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
        or name in TEST_CONFIG_FILES
    )


def parse_files(diff_text: str) -> List[Dict[str, object]]:
    """Per-file added/removed lines. A '--- ' line is a header only when '+++ ' follows."""
    lines = diff_text.splitlines()
    files: List[Dict[str, object]] = []
    current = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old = line[4:].split("\t")[0].strip()
            new = lines[i + 1][4:].split("\t")[0].strip()
            path = old if new == "/dev/null" else new
            if path[:2] in ("a/", "b/"):
                path = path[2:]
            current = {"file": path, "added": [], "removed": []}
            files.append(current)
            i += 1
        elif current is not None:
            if line.startswith("+"):
                current["added"].append(line[1:])
            elif line.startswith("-"):
                current["removed"].append(line[1:])
        i += 1
    return files


def touched_test_files(diff_text: str) -> List[str]:
    return [f["file"] for f in parse_files(diff_text) if is_test_path(f["file"])]


def scan_patch(diff_text: str) -> List[str]:
    """Human-readable tamper violations; empty list means clean."""
    violations: List[str] = []
    removed = added = 0
    for f in parse_files(diff_text):
        if not is_test_path(f["file"]):
            continue
        violations.append(f"patch modifies test file/config: {f['file']}")
        removed += sum(1 for l in f["removed"] if _ASSERT_RE.match(l))
        added += sum(1 for l in f["added"] if _ASSERT_RE.match(l))
        violations += [f"assert commented out in {f['file']}" for l in f["added"] if _COMMENTED_ASSERT_RE.match(l)]
        violations += [f"test skipped/xfailed in {f['file']}" for l in f["added"] if _SKIP_RE.search(l)]
    if removed > added:
        violations.append(f"{removed} test assertion(s) removed, only {added} added back")
    return violations