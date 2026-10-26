"""
Sandboxed Execution Harness for Dependency Resilience.
Runs tests in isolated environments, captures execution telemetry, and detects tampering.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is importable when this file is run directly (python engine/<file>.py)
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from engine.tamper import touched_test_files


def execute_test_suite(
    repo_path: str,
    test_cmd: Optional[List[str]] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Executes a test command inside the repository path and extracts ground-truth metrics.
    """
    if test_cmd is None:
        # Default to pytest with isolated module execution
        test_cmd = [sys.executable, "-m", "pytest", "-q", "-o", "filterwarnings=ignore"]

    # Clone environment and inject PYTHONPATH and isolated pytest settings
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{repo_path}{os.pathsep}{existing_pp}" if existing_pp else repo_path
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            test_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            env=env
        )
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        err_out = proc.stderr.strip()
        if not err_out and proc.returncode != 0:
            err_out = proc.stdout.strip()

        return {
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "raw_stderr": err_out,
            "execution_time_ms": elapsed_ms,
            "timed_out": False,
            "tampering_detected": False
        }
    except subprocess.TimeoutExpired as e:
        return {
            "exit_code": -1,
            "passed": False,
            "stdout": e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "raw_stderr": "Execution timed out.",
            "execution_time_ms": timeout * 1000,
            "timed_out": True,
            "tampering_detected": False
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "passed": False,
            "stdout": "",
            "raw_stderr": str(e),
            "execution_time_ms": 0,
            "timed_out": False,
            "tampering_detected": False
        }


def run_in_ephemeral_sandbox(
    target_repo_path: str,
    patch_diff: Optional[str] = None,
    test_cmd: Optional[List[str]] = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Copies the repository to an ephemeral temporary directory, applies the git patch if provided,
    verifies anti-tampering guards, and executes the test suite.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        sandbox_path = os.path.join(temp_dir, "sandbox_repo")
        
        # Copy repository ignoring .git to keep it fast
        def ignore_patterns(path, names):
            ignored = set()
            for name in names:
                if name in [".git", "__pycache__", ".venv", "venv", ".pytest_cache"]:
                    ignored.add(name)
            return ignored

        shutil.copytree(target_repo_path, sandbox_path, ignore=ignore_patterns)

        tampering_detected = False

        # Apply patch if provided
        if patch_diff and patch_diff.strip():
            # Check for illegal file touches (path components, not substrings: `pytest/`,
            # `latest/` and `contest.py` are ordinary source files)
            if touched_test_files(patch_diff):
                tampering_detected = True

            patch_file_path = os.path.join(temp_dir, "migration.patch")
            with open(patch_file_path, "w", encoding="utf-8") as f:
                f.write(patch_diff)

            # Try applying with git apply if git is initialized, or custom patch apply
            patch_applied = False
            try:
                # Initialize a temporary git repo so git apply works seamlessly
                subprocess.run(["git", "init"], cwd=sandbox_path, capture_output=True, text=True, check=False)
                subprocess.run(["git", "add", "-A"], cwd=sandbox_path, capture_output=True, text=True, check=False)
                
                apply_proc = subprocess.run(
                    ["git", "apply", "--ignore-whitespace", "--recount", patch_file_path],
                    cwd=sandbox_path,
                    capture_output=True,
                    text=True
                )
                if apply_proc.returncode == 0:
                    patch_applied = True
                else:
                    return {
                        "exit_code": 1,
                        "passed": False,
                        "stdout": "",
                        "raw_stderr": f"Patch application failed: {apply_proc.stderr}",
                        "execution_time_ms": 0,
                        "timed_out": False,
                        "tampering_detected": tampering_detected
                    }
            except Exception as e:
                return {
                    "exit_code": 1,
                    "passed": False,
                    "stdout": "",
                    "raw_stderr": f"Error applying patch: {str(e)}",
                    "execution_time_ms": 0,
                    "timed_out": False,
                    "tampering_detected": tampering_detected
                }

        # Run tests
        result = execute_test_suite(sandbox_path, test_cmd=test_cmd, timeout=timeout)
        if tampering_detected:
            result["tampering_detected"] = True

        return result


if __name__ == "__main__":
    print("[Person 1] Self-Testing engine/sandbox.py...")

    # Test 1: Direct command execution
    res = execute_test_suite(
        os.getcwd(),
        ["python", "-c", "import sys; print('Sandbox execution verified'); sys.exit(0)"]
    )
    print(f"\n[Test 1] Execution Result:\n  Exit Code: {res['exit_code']}\n  Passed: {res['passed']}\n  Stdout: {res['stdout']}\n  Time: {res['execution_time_ms']}ms")
    assert res["passed"] is True, "Test 1 failed!"

    # Test 2: Error capture
    res_err = execute_test_suite(
        os.getcwd(),
        ["python", "-c", "import sys; sys.stderr.write('Simulated ModuleNotFoundError\\n'); sys.exit(1)"]
    )
    print(f"\n[Test 2] Error Result:\n  Exit Code: {res_err['exit_code']}\n  Raw Stderr: {res_err['raw_stderr']}")
    assert res_err["passed"] is False, "Test 2 expected failure but passed!"
    assert "Simulated ModuleNotFoundError" in res_err["raw_stderr"]

    print("\nAll sandbox.py self-tests PASSED successfully!")