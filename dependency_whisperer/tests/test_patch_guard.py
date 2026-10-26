"""Pre-flight patch validation + its integration into the search loop."""
import difflib
import sys

import pytest

from engine.patch_guard import check_patch
from engine.search_loop import run_migration_search

ORIGINAL = "import oldlib\n\n\ndef load(path):\n    return oldlib.load(path)\n\n\nclass Thing:\n    pass\n"
TEST_FILE = "import mod\n\n\ndef test_load():\n    assert mod.load('x') == 'x'\n"


def _diff(new_text, original=ORIGINAL, name="mod.py"):
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True), new_text.splitlines(keepends=True),
        fromfile=f"a/{name}", tofile=f"b/{name}"))


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "mod.py").write_text(ORIGINAL)
    return tmp_path


def test_accepts_import_swap(repo):
    assert check_patch(str(repo), _diff(ORIGINAL.replace("import oldlib", "import newlib as oldlib")),
                       hero_file="mod.py").ok


def test_rejects_unrelated_file_body(repo):
    v = check_patch(str(repo), _diff("def check_site(site):\n    return site\n"), hero_file="mod.py")
    assert not v.ok and any("top-level definitions" in r for r in v.reasons)


def test_rejects_syntax_error(repo):
    v = check_patch(str(repo), _diff(ORIGINAL.replace("oldlib.load(path)", "oldlib.load((")), hero_file="mod.py")
    assert not v.ok and any("does not parse" in r for r in v.reasons)


def test_rejects_files_outside_scope(repo):
    (repo / "other.py").write_text(ORIGINAL)
    v = check_patch(str(repo), _diff(ORIGINAL.replace("oldlib", "newlib"), name="other.py"), hero_file="mod.py")
    assert not v.ok and any("outside the allowed set" in r for r in v.reasons)


def test_rejects_empty_patch(repo):
    assert not check_patch(str(repo), "  \n", hero_file="mod.py").ok


def test_large_rewrite_is_rejected_even_if_it_parses(tmp_path):
    big = "\n".join(f"def f{i}():\n    return {i}" for i in range(40)) + "\n"
    (tmp_path / "mod.py").write_text(big)
    # Keep every definition but gut the bodies: parses, keeps names, removes >40% of lines.
    gutted = "\n".join(f"def f{i}(): pass" for i in range(40)) + "\n"
    v = check_patch(str(tmp_path), _diff(gutted, original=big), hero_file="mod.py")
    assert not v.ok and any("should not rewrite" in r for r in v.reasons)


def test_search_loop_rejects_bad_patch_and_feeds_reason_back(repo):
    (repo / "test_mod.py").write_text(TEST_FILE)
    (repo / "mod.py").write_text("def load(path):\n    return path\n")
    original = "def load(path):\n    return path\n"
    seen_errors = []

    def generator(replacement, previous_error):
        seen_errors.append(previous_error)
        if not previous_error:
            return _diff("def check_site(site):\n    return site\n", original=original)
        return _diff("def load(path):\n    return path  # migrated\n", original=original)

    best, history, _ = run_migration_search(
        repo_path=str(repo), target_pkg="oldlib", replacement_pkg="newlib", hero_file="mod.py",
        patch_generator_fn=generator, test_cmd=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
    )
    assert [n.status for n in history] == ["BASELINE", "REJECTED", "PASSED"]
    assert history[1].reward_score < 0
    assert "rejected before execution" in seen_errors[1]
    assert best.node_id == "node_2"