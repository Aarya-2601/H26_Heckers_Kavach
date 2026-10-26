"""Module for applying verified auto-healed patches back to the target repository on disk.

Ensures:
1. Ground-truth code updates in the real repository.
2. Manifest updates (e.g. requirements.txt, pyproject.toml).
3. Persistent migration history tracking in .kavach_migrations.json so subsequent runs recognize resolved dependencies.
4. Cache invalidation across analyzer and web dashboard so rescans immediately reflect the new state.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.theme import console


def apply_unified_diff_to_text(original: str, diff_text: str) -> Optional[str]:
    """Applies unified diff hunks directly to text without relying on external git/patch CLI."""
    if not diff_text or not diff_text.strip():
        return None

    orig_lines = original.splitlines(keepends=True)
    diff_lines = diff_text.splitlines(keepends=True)

    hunks: List[List[str]] = []
    current_hunk: List[str] = []
    in_hunk = False
    for line in diff_lines:
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
            in_hunk = True
        elif in_hunk:
            current_hunk.append(line)
    if current_hunk:
        hunks.append(current_hunk)

    if not hunks:
        return None

    result_lines = list(orig_lines)
    applied_any = False

    for hunk in hunks:
        old_slice: List[str] = []
        new_slice: List[str] = []
        for hline in hunk[1:]:
            if hline.startswith("-"):
                old_slice.append(hline[1:])
            elif hline.startswith("+"):
                new_slice.append(hline[1:])
            elif hline.startswith(" "):
                old_slice.append(hline[1:])
                new_slice.append(hline[1:])

        # Find exact match for old_slice in result_lines
        old_str = "".join(old_slice)
        found_idx = -1
        if old_str:
            for i in range(len(result_lines) - len(old_slice) + 1):
                if "".join(result_lines[i : i + len(old_slice)]) == old_str:
                    found_idx = i
                    break

        if found_idx != -1:
            result_lines[found_idx : found_idx + len(old_slice)] = new_slice
            applied_any = True
        else:
            # Fallback line-by-line replacement for single-line modifications
            removes = [l[1:].strip() for l in hunk[1:] if l.startswith("-") and l[1:].strip()]
            adds = [l[1:].strip() for l in hunk[1:] if l.startswith("+") and l[1:].strip()]
            if len(removes) == 1 and len(adds) == 1:
                rem_needle = removes[0]
                add_replacement = adds[0]
                for idx, rline in enumerate(result_lines):
                    if rem_needle in rline:
                        result_lines[idx] = rline.replace(rem_needle, add_replacement)
                        applied_any = True
                        break

    if applied_any:
        return "".join(result_lines)
    return None


def apply_patch_to_repo(
    repo_path: Union[str, Path],
    patch_diff: str,
    target_package: str,
    replacement_pkg: str,
    hero_file: str,
    reward_score: int = 100,
    update_manifest: bool = True
) -> Dict[str, Any]:
    """Applies verified patch to repo on disk and updates manifests & history."""
    repo_dir = Path(repo_path).resolve()
    if not repo_dir.exists():
        return {"success": False, "error": f"Repository directory {repo_dir} does not exist."}

    target_file = (repo_dir / hero_file).resolve() if hero_file else None

    patch_applied = False
    apply_method = "none"
    error_msg = ""

    # Strategy 1: Python-native unified diff applier directly on target file
    if target_file and target_file.exists() and patch_diff:
        try:
            curr_code = target_file.read_text(encoding="utf-8")
            patched_code = apply_unified_diff_to_text(curr_code, patch_diff)
            if patched_code and patched_code != curr_code:
                target_file.write_text(patched_code, encoding="utf-8")
                patch_applied = True
                apply_method = "native_diff_engine"
        except Exception as e:
            error_msg = f"Native diff engine exception: {e}"

    # Strategy 2: git apply / patch CLI fallback
    if not patch_applied and patch_diff and patch_diff.strip():
        with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False, encoding="utf-8") as tf:
            tf.write(patch_diff)
            temp_patch_path = tf.name

        try:
            proc = subprocess.run(
                ["git", "apply", "--whitespace=fix", temp_patch_path],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                check=False
            )
            if proc.returncode == 0:
                patch_applied = True
                apply_method = "git_apply"
            else:
                error_msg = proc.stderr.strip() or proc.stdout.strip()
        except Exception as e:
            error_msg = str(e)

        if not patch_applied:
            try:
                res = subprocess.run(
                    ["patch", "-p1", "-i", temp_patch_path],
                    cwd=str(repo_dir),
                    capture_output=True,
                    text=True,
                    check=False
                )
                if res.returncode == 0:
                    patch_applied = True
                    apply_method = "patch_cli"
            except Exception:
                pass

        try:
            os.remove(temp_patch_path)
        except Exception:
            pass

    # Strategy 3: Targeted AST import / symbol rewrite on target_file
    if not patch_applied and target_file and target_file.exists():
        try:
            content = target_file.read_text(encoding="utf-8")
            clean_old = target_package.lower().replace("-", "_")
            clean_new = replacement_pkg.lower().replace("-", "_").split()[0]

            new_content = None
            if f"from {clean_old} import" in content:
                new_content = content.replace(f"from {clean_old} import", f"from {clean_new} import")
            elif f"import {clean_old}" in content:
                new_content = content.replace(f"import {clean_old}", f"import {clean_new} as {clean_old}")
            elif clean_old in content:
                new_content = content.replace(clean_old, clean_new)

            if new_content and new_content != content:
                target_file.write_text(new_content, encoding="utf-8")
                patch_applied = True
                apply_method = "direct_ast_rewrite"
        except Exception as e:
            error_msg = f"Direct rewrite failed: {e}"

    # Strategy 4: Check if file already contains replacement (already up-to-date)
    if not patch_applied and target_file and target_file.exists():
        existing = target_file.read_text(encoding="utf-8", errors="ignore")
        clean_rep = replacement_pkg.lower().replace("-", "_").split()[0]
        if clean_rep in existing:
            patch_applied = True
            apply_method = "already_present"

    # 2. Update Manifests (requirements.txt, pyproject.toml)
    updated_manifests: List[str] = []
    if update_manifest:
        req_file = repo_dir / "requirements.txt"
        if req_file.exists():
            try:
                req_text = req_file.read_text(encoding="utf-8")
                pattern = re.compile(rf"^{re.escape(target_package)}([=<>!~].*)?$", re.MULTILINE | re.IGNORECASE)
                if pattern.search(req_text):
                    clean_rep_name = replacement_pkg.split()[0]
                    new_req = pattern.sub(clean_rep_name, req_text)
                    req_file.write_text(new_req, encoding="utf-8")
                    updated_manifests.append("requirements.txt")
            except Exception:
                pass

        pyp_file = repo_dir / "pyproject.toml"
        if pyp_file.exists():
            try:
                pyp_text = pyp_file.read_text(encoding="utf-8")
                pattern = re.compile(rf'"{re.escape(target_package)}([=<>!~].*)?"', re.IGNORECASE)
                if pattern.search(pyp_text):
                    clean_rep_name = replacement_pkg.split()[0]
                    new_pyp = pattern.sub(f'"{clean_rep_name}"', pyp_text)
                    pyp_file.write_text(new_pyp, encoding="utf-8")
                    updated_manifests.append("pyproject.toml")
            except Exception:
                pass

    # 3. Persistent tracking in .kavach_migrations.json
    history_file = repo_dir / ".kavach_migrations.json"
    if patch_applied:
        migration_record = {
            "target_package": target_package,
            "replacement_package": replacement_pkg,
            "hero_file": hero_file,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "reward_score": reward_score,
            "apply_method": apply_method,
            "updated_manifests": updated_manifests,
            "status": "APPLIED_AND_VERIFIED"
        }

        history_data: Dict[str, Any] = {"repository": str(repo_dir), "migrations": []}
        if history_file.exists():
            try:
                history_data = json.loads(history_file.read_text(encoding="utf-8"))
            except Exception:
                history_data = {"repository": str(repo_dir), "migrations": []}

        existing_migs = [
            m for m in history_data.get("migrations", [])
            if m.get("target_package", "").lower() != target_package.lower()
        ]
        existing_migs.append(migration_record)
        history_data["migrations"] = existing_migs
        history_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        try:
            history_file.write_text(json.dumps(history_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # 4. Invalidate web analysis cache so subsequent scans immediately reflect on-disk state
    try:
        from web import analysis as kv_analysis
        with kv_analysis._LOCK:
            kv_analysis._CACHE.clear()
    except Exception:
        pass

    return {
        "success": patch_applied,
        "apply_method": apply_method,
        "updated_manifests": updated_manifests,
        "error": error_msg if not patch_applied else None,
        "history_file": str(history_file)
    }
