"""Anti-tamper checks must be scoped to real test files, not substrings or source asserts."""
import difflib
import sys

import pytest

import analyzer.auditor as auditor
from engine.rewards import compute_reward
from engine.sandbox import run_in_ephemeral_sandbox
from engine.tamper import is_test_path, scan_patch, touched_test_files

PASS_CMD = [sys.executable, "-c", "pass"]

SRC = "def f(x):\n    assert x > 0\n    return x\n"
SRC_NO_ASSERT = "def f(x):\n    return x\n"


def _diff(old, new, path):
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True), fromfile=f"a/{path}", tofile=f"b/{path}"))


PATHS = [
    "src/black/__init__.py", "src/pytest_helpers/latest/contest.py", "src/attestation.py", "src/protest/handler.py",
    "tests/test_a.py", "test/helpers.py", "pkg/test_util.py", "pkg/util_test.py", "pkg/x.spec.js",
    "conftest.py", "pytest.ini", ".audit_tests/test_red_team.py", "pkg/tests/data.json", "C:\\r\\tests\\a.py",
]


@pytest.mark.parametrize("path", PATHS)
def test_is_test_path_agrees_with_auditor(path):
    assert is_test_path(path) == auditor.is_test_path(path)


@pytest.mark.parametrize("path", [
    "src/pytest_helpers/latest/contest.py", "src/attestation.py", "src/protest/handler.py", "src/black/__init__.py",
])
def test_substring_paths_are_not_test_files(path):
    assert not is_test_path(path)
    assert touched_test_files(_diff(SRC, SRC_NO_ASSERT, path)) == []


@pytest.mark.parametrize("path", ["src/latest/mod.py", "src/pytest_helpers/mod.py"])
def test_sandbox_does_not_flag_substring_paths(tmp_path, path):
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(SRC)
    res = run_in_ephemeral_sandbox(str(tmp_path), patch_diff=_diff(SRC, SRC_NO_ASSERT, path), test_cmd=PASS_CMD)
    assert res["passed"] and res["tampering_detected"] is False


def test_sandbox_flags_real_test_file_edits(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x():\n    assert 1\n")
    patch = _diff("def test_x():\n    assert 1\n", "def test_x():\n    pass\n", "tests/test_x.py")
    res = run_in_ephemeral_sandbox(str(tmp_path), patch_diff=patch, test_cmd=PASS_CMD)
    assert res["tampering_detected"] is True


@pytest.fixture(params=["auditor", "fallback"])
def reward_mode(request, monkeypatch):
    """Run each reward test with Person 2's auditor and with the built-in fallback."""
    if request.param == "fallback":
        def boom(*a, **k):
            raise RuntimeError("auditor unavailable")
        monkeypatch.setattr(auditor, "audit_patch", boom)
    return request.param


OK_RUN = {"exit_code": 0, "passed": True, "execution_time_ms": 10, "raw_stderr": "", "tampering_detected": False}


def test_removing_assert_from_source_is_not_tampering(reward_mode):
    score, breakdown = compute_reward(OK_RUN, _diff(SRC, SRC_NO_ASSERT, "src/black/__init__.py"))
    assert breakdown["tampering_detected"] is False and score > 0


def test_removing_assert_from_tests_is_tampering(reward_mode):
    patch = _diff("def test_x():\n    assert 1\n", "def test_x():\n    pass\n", "tests/test_x.py")
    score, breakdown = compute_reward(OK_RUN, patch)
    assert breakdown["tampering_detected"] is True and score == -9999


def test_fallback_scan_catches_skip_and_commented_assert():
    patch = _diff("def test_x():\n    assert 1\n", "def test_x():\n    # assert 1\n    pytest.skip('no')\n",
                  "tests/test_x.py")
    text = " ".join(scan_patch(patch))
    assert "commented out" in text and "skipped" in text