"""
Person 2: Test suite inspector (AST).

Reads the repo's test files WITHOUT running them and records:
  - every test (name, line, number of assert statements, fixtures it asks for)
  - which project functions/classes each test touches (e.g. linkwatch.checker.check_site)
  - the fixtures defined in conftest.py
  - a SHA-256 of each test file (baseline to prove nobody edited the tests later)
  - assert_literals: values the tests expect -> feed to auditor.audit_patch(test_literals=...)

Named suite_inspector.py (not test_*.py) so pytest never tries to collect it.

Run:
    python analyzer/suite_inspector.py <tests_dir>                      # package defaults to 'linkwatch'
    python analyzer/suite_inspector.py <tests_dir> <package> out.json   # also save JSON
"""
import ast
import hashlib
import json
import os
import sys

try:
    from analyzer.ast_scanner import dotted
    from analyzer.auditor import IGNORED_LITERALS
except ImportError:  # running the file directly
    from ast_scanner import dotted
    from auditor import IGNORED_LITERALS

SKIP_DIRS = {".git", "venv", ".venv", "env", "node_modules", "__pycache__", ".tox"}


def is_suite_file(name):
    return name.endswith(".py") and (
        name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
    )


def project_imports(tree, package):
    """local name -> full dotted origin, for imports of the project's own package."""
    origins = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] == package:
                    origins[a.asname or package] = a.name if a.asname else package
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module and node.module.split(".")[0] == package:
                for a in node.names:
                    origins[a.asname or a.name] = f"{node.module}.{a.name}"
    return origins


def project_refs(node, origins):
    """Project symbols used inside `node`, e.g. {'linkwatch.cache.save_results'}."""
    found = set()
    for n in ast.walk(node):
        if isinstance(n, (ast.Name, ast.Attribute)) and isinstance(n.ctx, ast.Load):
            d = dotted(n)
            if not d:
                continue
            root, _, rest = d.partition(".")
            if root in origins:
                found.add(origins[root] + (f".{rest}" if rest else ""))
    # keep only the most specific ones ('linkwatch.cache' is dropped if 'linkwatch.cache.save_results' exists)
    return {r for r in found if not any(o != r and o.startswith(r + ".") for o in found)}


def _const_values(root, skip_ids, lits):
    for c in ast.walk(root):
        if not isinstance(c, ast.Constant) or id(c) in skip_ids:
            continue
        v = c.value
        if isinstance(v, (bool, type(None), bytes)):
            continue
        if isinstance(v, int) and 100 <= v <= 599:
            continue
        lits.add(str(v))


def assert_literals(node):
    """
    String/number values the tests expect: inside `assert ...` AND inside
    self.assertEqual(...) / mock.assert_called_with(...) style calls.
    Skips dict keys like result["up"] and HTTP status codes (100-599) to avoid false flags.
    """
    lits = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Assert):
            keys = {id(s.slice) for s in ast.walk(n) if isinstance(s, ast.Subscript)}
            _const_values(n, keys, lits)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert"):
            keys = {id(s.slice) for s in ast.walk(n) if isinstance(s, ast.Subscript)}
            _const_values(n, keys, lits)
    return lits - IGNORED_LITERALS


def count_asserts(func):
    """`assert x` statements plus self.assertEqual(...) / mock.assert_called_with(...) calls."""
    return sum(
        isinstance(n, ast.Assert)
        or (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert"))
        for n in ast.walk(func)
    )


def is_test_class(node):
    """pytest classes start with 'Test'; unittest classes can have any name but subclass TestCase."""
    if node.name.startswith("Test"):
        return True
    return any((dotted(b) or "").split(".")[-1] == "TestCase" for b in node.bases)


def is_fixture(func):
    for dec in func.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if dotted(target) in ("pytest.fixture", "fixture"):
            return True
    return False


def inspect_file(path, rel_path, package):
    with open(path, "rb") as f:
        raw = f.read()
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=rel_path)
    except (SyntaxError, UnicodeDecodeError):
        return None

    origins = project_imports(tree, package)
    fixtures, tests, literals = [], [], set()

    def add_test(func, prefix=""):
        tests.append({
            "name": prefix + func.name,
            "line": func.lineno,
            "asserts": count_asserts(func),
            "args": [a.arg for a in func.args.args if a.arg != "self"],
            "project_refs": sorted(project_refs(func, origins)),
        })
        literals.update(assert_literals(func))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_fixture(node):
                fixtures.append(node.name)
            elif node.name.startswith("test"):
                add_test(node)
        elif isinstance(node, ast.ClassDef) and is_test_class(node):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                    add_test(item, prefix=node.name + ".")

    return {
        "file": rel_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "fixtures": fixtures,
        "tests": tests,
        "_literals": literals,
    }


def inspect_suite(tests_dir, package="linkwatch"):
    if not os.path.isdir(tests_dir):
        raise SystemExit(f"ERROR: tests folder not found: {os.path.abspath(tests_dir)}")
    files, unparsed, all_literals, all_refs = [], [], set(), set()

    for root, dirs, names in os.walk(tests_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if not is_suite_file(name):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, tests_dir).replace(os.sep, "/")
            info = inspect_file(path, rel, package)
            if info is None:
                unparsed.append(rel)
                continue
            all_literals |= info.pop("_literals")
            for t in info["tests"]:
                all_refs.update(t["project_refs"])
            files.append(info)

    return {
        "package": package,
        "total_files": len(files),
        "total_tests": sum(len(f["tests"]) for f in files),
        "total_asserts": sum(t["asserts"] for f in files for t in f["tests"]),
        "project_refs": sorted(all_refs),
        "assert_literals": sorted(all_literals),
        "files": files,
        "unparsed": unparsed,
    }


if __name__ == "__main__":
    tests_dir = sys.argv[1] if len(sys.argv) > 1 else "tests"
    package = sys.argv[2] if len(sys.argv) > 2 else "linkwatch"

    report = inspect_suite(tests_dir, package)
    print(f"[Person 2] Inspected '{tests_dir}' (project package: {package})")
    print(f"Files: {report['total_files']}   Tests: {report['total_tests']}   Asserts: {report['total_asserts']}")
    for f in report["files"]:
        if f["fixtures"]:
            print(f"\n{f['file']}  (fixtures: {', '.join(f['fixtures'])})")
        else:
            print(f"\n{f['file']}")
        for t in f["tests"]:
            refs = ", ".join(t["project_refs"]) or "-"
            print(f"  line {t['line']:<3} {t['name']:<28} asserts={t['asserts']}  touches: {refs}")
    if report["total_files"] == 0:
        print(f"WARNING: no test_*.py / *_test.py / conftest.py under {os.path.abspath(tests_dir)} - wrong folder?")
    if report["unparsed"]:
        print("\nCould not parse:", ", ".join(report["unparsed"]))

    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nSaved -> {sys.argv[3]}")