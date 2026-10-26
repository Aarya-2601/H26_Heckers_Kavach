"""
Pre-flight patch validation.

A model (or a fallback) can return something that is syntactically a diff but is not a
migration: an unrelated file body, a truncated file, a rewrite of the wrong file. Running
such a patch through the sandbox wastes a search attempt and, worse, can score well by
accident. These checks are repository-agnostic and run before any test execution:

  1. The patch only touches the files it is allowed to touch (default: the hero file).
  2. The patch applies cleanly to the original file.
  3. The patched file still parses.
  4. Every top-level function/class the original defined is still defined.
  5. The patch does not delete most of the original file.
"""

import ast
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

# A migration is treated as a rewrite when it removes more than this fraction of the original
# file AND at least MIN_REMOVED_LINES lines (so a 1-line change in a tiny file is never flagged).
MAX_REMOVED_FRACTION = 0.4
MIN_REMOVED_LINES = 10


@dataclass
class PatchVerdict:
    ok: bool
    reasons: List[str] = field(default_factory=list)
    stats: Dict[str, object] = field(default_factory=dict)

    def summary(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "ok"


def _norm(path: str) -> str:
    path = path.strip().split("\t")[0].replace("\\", "/")
    for prefix in ("a/", "b/"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    return path[2:] if path.startswith("./") else path


def patch_targets(patch_diff: str) -> Set[str]:
    """Files named by the diff's ---/+++ headers (excluding /dev/null)."""
    targets: Set[str] = set()
    for line in patch_diff.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            raw = line[4:].strip()
            if raw.startswith("/dev/null"):
                continue
            targets.add(_norm(raw))
    return targets


def _top_level_names(tree: ast.AST) -> Set[str]:
    names: Set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def check_patch(
    repo_path: str,
    patch_diff: str,
    hero_file: Optional[str] = None,
    allowed_files: Optional[Iterable[str]] = None,
    max_removed_fraction: float = MAX_REMOVED_FRACTION,
) -> PatchVerdict:
    """Validate `patch_diff` against the original files in `repo_path`.

    `allowed_files` defaults to {hero_file}. With neither given, the file-scope check is skipped.
    """
    if not patch_diff or not patch_diff.strip():
        return PatchVerdict(False, ["patch is empty"])

    reasons: List[str] = []
    stats: Dict[str, object] = {}

    targets = patch_targets(patch_diff)
    if not targets:
        return PatchVerdict(False, ["patch has no ---/+++ file headers"])

    allowed = {_norm(f) for f in (allowed_files or ([hero_file] if hero_file else []))}
    if allowed:
        extra = sorted(targets - allowed)
        if extra:
            reasons.append(f"patch touches files outside the allowed set: {', '.join(extra)}")

    # Work on a scratch copy of only the files the patch names, so the real repo is never touched.
    scratch = tempfile.mkdtemp(prefix="kavach_guard_")
    try:
        originals: Dict[str, Optional[str]] = {}
        for rel in targets:
            src = os.path.join(repo_path, rel)
            dst = os.path.join(scratch, rel)
            os.makedirs(os.path.dirname(dst) or scratch, exist_ok=True)
            if os.path.isfile(src):
                shutil.copyfile(src, dst)
                with open(src, "r", encoding="utf-8", errors="replace", newline="") as fh:
                    originals[rel] = fh.read()
            else:
                originals[rel] = None

        patch_path = os.path.join(scratch, "__kavach__.patch")
        with open(patch_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(patch_diff)

        try:
            proc = subprocess.run(
                ["git", "apply", "--ignore-whitespace", "--recount", patch_path],
                cwd=scratch, capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            reasons.append(f"could not run git apply for validation: {exc}")
            return PatchVerdict(False, reasons, stats)
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout).strip().splitlines()
            reasons.append("patch does not apply to the original file: " + (msg[0] if msg else "unknown error"))
            return PatchVerdict(False, reasons, stats)

        for rel in sorted(targets):
            if not rel.endswith(".py"):
                continue
            patched_path = os.path.join(scratch, rel)
            if not os.path.isfile(patched_path):
                reasons.append(f"{rel}: patch deletes the file")
                continue
            with open(patched_path, "r", encoding="utf-8", errors="replace", newline="") as fh:
                patched = fh.read()

            try:
                patched_tree = ast.parse(patched)
            except SyntaxError as exc:
                reasons.append(f"{rel}: patched file does not parse ({exc.msg}, line {exc.lineno})")
                continue

            original = originals.get(rel)
            if original is None:
                continue  # new file: nothing to compare against

            orig_lines = original.splitlines()
            removed = sum(
                1 for l in patch_diff.splitlines()
                if l.startswith("-") and not l.startswith("---")
            ) if len(targets) == 1 else None
            if removed is not None and orig_lines:
                fraction = removed / len(orig_lines)
                stats[f"{rel}:removed_fraction"] = round(fraction, 3)
                if fraction > max_removed_fraction and removed >= MIN_REMOVED_LINES:
                    reasons.append(
                        f"{rel}: patch removes {removed} of {len(orig_lines)} lines "
                        f"({fraction:.0%}); a dependency migration should not rewrite the file"
                    )

            try:
                original_names = _top_level_names(ast.parse(original))
            except SyntaxError:
                original_names = set()  # original already unparsable: cannot compare API
            lost = sorted(original_names - _top_level_names(patched_tree))
            if lost:
                shown = ", ".join(lost[:8]) + (f" (+{len(lost) - 8} more)" if len(lost) > 8 else "")
                reasons.append(f"{rel}: patch removes top-level definitions: {shown}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    return PatchVerdict(not reasons, reasons, stats)


if __name__ == "__main__":
    import difflib

    print("[Person 1] Self-testing engine/patch_guard.py...")
    with tempfile.TemporaryDirectory() as repo:
        original = "import oldlib\n\n\ndef load(path):\n    return oldlib.load(path)\n\n\nclass Thing:\n    pass\n"
        with open(os.path.join(repo, "mod.py"), "w", newline="") as fh:
            fh.write(original)

        def diff_for(new_text: str, name: str = "mod.py") -> str:
            return "".join(difflib.unified_diff(
                original.splitlines(keepends=True), new_text.splitlines(keepends=True),
                fromfile=f"a/{name}", tofile=f"b/{name}"))

        good = diff_for(original.replace("import oldlib", "import newlib as oldlib"))
        assert check_patch(repo, good, hero_file="mod.py").ok

        unrelated = diff_for("def check_site(site):\n    return site\n")
        v = check_patch(repo, unrelated, hero_file="mod.py")
        assert not v.ok and any("top-level definitions" in r for r in v.reasons), v

        broken = diff_for(original.replace("return oldlib.load(path)", "return oldlib.load(("))
        v = check_patch(repo, broken, hero_file="mod.py")
        assert not v.ok and any("does not parse" in r for r in v.reasons), v

        wrong_file = good.replace("mod.py", "other.py")
        v = check_patch(repo, wrong_file, hero_file="mod.py")
        assert not v.ok, v

        assert not check_patch(repo, "", hero_file="mod.py").ok
    print("All patch_guard.py self-tests PASSED successfully!")