"""
Reward Scoring Engine for Dependency Resilience Migration.
Evaluates sandboxed execution telemetry and generated patches deterministically.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Set

# Ensure project root is importable when this file is run directly (python engine/<file>.py)
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from engine.tamper import scan_patch


def compute_reward(
    run_result: Dict[str, Any],
    patch_diff: str = "",
    baseline_time_ms: int = 150,
    seen_error_signatures: Optional[Set[str]] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes deterministic score based on sandboxed execution results and patch analysis.
    
    Returns:
        score: Total integer reward score
        breakdown: Detailed dictionary explaining every reward / penalty component
    """
    score = 0
    breakdown = {
        "extrinsic_reward": 0,
        "intrinsic_curiosity": 0,
        "anti_cheat_penalty": 0,
        "efficiency_penalty": 0,
        "code_bloat_penalty": 0,
        "tampering_detected": False,
        "reasons": []
    }

    # 1. Anti-Cheat & Tampering Checks (-9999 points)
    is_tampering = run_result.get("tampering_detected", False)
    
    # Run Person 2's deep AST auditor if available
    auditor_ran = False
    if patch_diff:
        try:
            from analyzer.auditor import audit_patch
            audit_res = audit_patch(patch_diff)
            auditor_ran = True
            if audit_res.get("tampering_detected"):
                is_tampering = True
                for v in audit_res.get("violations", []):
                    breakdown["reasons"].append(f"Auditor violation: {v}")
        except Exception as exc:
            breakdown["reasons"].append(
                f"Auditor unavailable ({type(exc).__name__}: {exc}); using built-in scoped checks."
            )

    # Fallback: scoped checks (test files only, matched by path component) if the auditor did not run
    if patch_diff and not auditor_ran and not is_tampering:
        for violation in scan_patch(patch_diff):
            is_tampering = True
            breakdown["reasons"].append(f"Anti-cheat trigger: {violation}")

    if is_tampering:
        score -= 9999
        breakdown["anti_cheat_penalty"] = -9999
        breakdown["tampering_detected"] = True
        return score, breakdown

    # 2. Extrinsic Reward (+100 points for test pass)
    test_passed = run_result.get("passed", False) or run_result.get("exit_code") == 0
    if test_passed:
        score += 100
        breakdown["extrinsic_reward"] = 100
        breakdown["reasons"].append("Extrinsic goal achieved: Sandboxed tests passed cleanly (+100).")
    else:
        # 3. Intrinsic Curiosity Reward (+30 points for encountering new error signatures)
        raw_stderr = run_result.get("raw_stderr", "")
        error_is_new = run_result.get("error_is_new", False)
        
        if seen_error_signatures is not None and raw_stderr:
            # Simple heuristic signature extraction: take last non-empty line of stderr (typically exception name)
            stderr_lines = [l.strip() for l in raw_stderr.splitlines() if l.strip()]
            sig = stderr_lines[-1] if stderr_lines else "UnknownError"
            if sig not in seen_error_signatures:
                seen_error_signatures.add(sig)
                error_is_new = True

        if error_is_new:
            score += 30
            breakdown["intrinsic_curiosity"] = 30
            breakdown["reasons"].append("Intrinsic curiosity bonus: Discovered new error signature (+30).")

    # 4. Efficiency Penalty (-10 points if slower than baseline)
    exec_time = run_result.get("execution_time_ms", 0)
    if baseline_time_ms > 0 and exec_time > baseline_time_ms:
        score -= 10
        breakdown["efficiency_penalty"] = -10
        breakdown["reasons"].append(f"Efficiency penalty: Execution ({exec_time}ms) exceeded baseline ({baseline_time_ms}ms) (-10).")

    # 5. Code Bloat / Mutation Penalty (-1 point per added line of code to favor minimal shims)
    if patch_diff:
        added_lines = sum(
            1 for line in patch_diff.splitlines() 
            if line.startswith("+") and not line.startswith("+++")
        )
        bloat_penalty = added_lines * 1
        score -= bloat_penalty
        breakdown["code_bloat_penalty"] = -bloat_penalty
        breakdown["reasons"].append(f"Code bloat penalty: {added_lines} lines added in diff (-{bloat_penalty}).")

    return score, breakdown


if __name__ == "__main__":
    print("[Person 1] Self-Testing engine/rewards.py...")

    # Case 1: Clean Pass with small diff
    result_pass = {
        "exit_code": 0,
        "passed": True,
        "execution_time_ms": 110,
        "raw_stderr": "",
        "tampering_detected": False
    }
    diff_clean = "--- a/src/client.py\n+++ b/src/client.py\n@@ -1,2 +1,2 @@\n-import requests\n+import httpx"
    score, breakdown = compute_reward(result_pass, diff_clean, baseline_time_ms=150)
    print(f"\n[Case 1 - Clean Pass] Score: {score}")
    print(f"Breakdown: {breakdown}")
    assert score == 99, f"Expected 99 (100 - 1 added line), got {score}"

    # Case 2: Cheating attempt (deleted assertion)
    diff_cheat = "--- a/tests/test_api.py\n+++ b/tests/test_api.py\n-    assert response.status_code == 200"
    score_cheat, breakdown_cheat = compute_reward(result_pass, diff_cheat)
    print(f"\n[Case 2 - Cheating Attempt] Score: {score_cheat}")
    print(f"Breakdown: {breakdown_cheat}")
    assert score_cheat == -9999, f"Expected -9999, got {score_cheat}"

    # Case 3: Failed run with new error signature
    seen_errors = set()
    result_fail = {
        "exit_code": 1,
        "passed": False,
        "execution_time_ms": 130,
        "raw_stderr": "Traceback (most recent call last):\nModuleNotFoundError: No module named 'httpx'",
        "tampering_detected": False
    }
    score_fail, breakdown_fail = compute_reward(result_fail, "", seen_error_signatures=seen_errors)
    print(f"\n[Case 3 - New Error Explored] Score: {score_fail}")
    print(f"Breakdown: {breakdown_fail}")
    assert score_fail == 30, f"Expected 30 curiosity reward, got {score_fail}"

    print("\nAll rewards.py self-tests PASSED successfully!")