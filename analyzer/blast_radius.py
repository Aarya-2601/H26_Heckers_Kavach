"""Person 2: blast radius score, hero file, and tree data for Person 4's renderer."""
from collections import Counter


def compute_blast_radius(call_sites):
    """
    call_sites: list of dicts, each with at least a 'file' key.
    Score = min(100, files_affected * 20 + total_call_sites * 5)
    Hero file = file with the most call sites (ties -> alphabetical first).
    """
    per_file = Counter(cs["file"] for cs in call_sites)
    files_affected = len(per_file)
    total = len(call_sites)
    score = min(100, files_affected * 20 + total * 5)

    hero_file = None
    if per_file:
        hero_file = max(sorted(per_file), key=lambda f: per_file[f])

    return {
        "score": score,
        "files_affected": files_affected,
        "total_call_sites": total,
        "hero_file": hero_file,
        "per_file": dict(per_file),
    }


def build_tree_data(target_pkg, call_sites):
    """
    Nested dict for Person 4's rich.tree.Tree:
    {"name": pkg, "children": [{"name": file, "children": [{"name": "line 5: fn() -> symbol"}]}]}
    """
    by_file = {}
    for cs in call_sites:
        by_file.setdefault(cs["file"], []).append(cs)

    children = []
    for file in sorted(by_file):
        leaves = []
        for cs in sorted(by_file[file], key=lambda c: c["line"]):
            what = cs.get("symbol") or cs.get("code_snippet", "")
            fn = cs["calling_function"]
            where = fn if fn.startswith(("<", "class ")) else f"{fn}()"   # no '<module>()' / 'class X()'
            leaves.append({"name": f"line {cs['line']}: {where} -> {what}"})
        children.append({"name": file, "children": leaves})

    return {"name": target_pkg, "children": children}