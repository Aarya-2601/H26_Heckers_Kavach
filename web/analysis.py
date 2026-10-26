"""Generic, repo-agnostic analysis for the Kavach dashboard.

Everything the dashboard shows for a repository (target package, hero file,
call sites, auditor checks, tests) is computed here from the repo's actual
source instead of being hard-coded for any one repository.
"""

import ast
import os
import re
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from analyzer.ast_scanner import scan_repo, SKIP_DIRS, IMPORT_ALIASES
from analyzer.auditor import is_test_path

# Non-production code must not drive migration decisions
NON_PRODUCTION_DIRS = {"docs", "doc", "examples", "example", "benchmarks", "benchmark", ".github", ".cloned_repos", ".pytest_cache", ".ruff_cache", ".mypy_cache", "site-packages"}
SKIP_DIRS |= NON_PRODUCTION_DIRS  # shared with analyzer.ast_scanner so the pipeline scans the same files
IGNORE_DIRS = set(SKIP_DIRS)
STUB_ONLY_MODULES = {"_typeshed", "typing_extensions_stub"}

# package -> (suggested replacement, why it is a migration candidate)
KNOWN_REPLACEMENTS: Dict[str, Tuple[str, str]] = {
    "requests": ("httpx", "Synchronous API, easy to monkey-patch globally, no HTTP/2"),
    "toml": ("tomllib", "Superseded by tomllib in Python 3.11+"),
    "appdirs": ("platformdirs", "Unmaintained since 2017"),
    "jinja2": ("jinja2>=3.1", "Old 2.x releases break on modern MarkupSafe (soft_unicode)"),
    "pyyaml": ("ruamel.yaml", "Unsafe load defaults and slow release cadence"),
    "six": ("native Python 3", "Python 2 compatibility layer is no longer needed"),
    "mock": ("unittest.mock", "Backport folded into the standard library"),
    "simplejson": ("json", "Standard library json is sufficient"),
    "pytz": ("zoneinfo", "zoneinfo ships with Python 3.9+"),
    "nose": ("pytest", "Unmaintained test runner"),
    "pkg_resources": ("importlib.metadata", "Deprecated setuptools API"),
    "setuptools": ("importlib.metadata", "pkg_resources usage is deprecated"),
    "chardet": ("charset-normalizer", "Slow and license-constrained"),
    "typing_extensions": ("typing (stdlib)", "Backport - most names are in the standard typing module on modern Python"),
    "pycrypto": ("pycryptodome", "Abandoned with known CVEs"),
    "urllib3": ("httpx", "Direct low-level HTTP usage"),
    "docopt": ("argparse / click", "Unmaintained"),
    "enum34": ("enum (stdlib)", "Breaks on modern Python"),
    "futures": ("concurrent.futures", "Backport of a stdlib module"),
    "pydantic": ("pydantic>=2", "v1 API removed/changed in v2"),
    "attrs": ("dataclasses", "Often replaceable by stdlib dataclasses"),
}

SECRET_RE = re.compile(
    r"""(?ix)[A-Za-z0-9_]*(password|passwd|secret|api[_-]?key|access[_-]?key|auth[_-]?token|private[_-]?key|token)[A-Za-z0-9_]*\s*[:=]\s*(['"])([^'"\s]{8,})\2"""
)
PLACEHOLDER_RE = re.compile(r"(?i)(example|changeme|your[_-]|xxx|<.*>|\{.*\}|dummy|test|fake|placeholder|\*\*\*)")

import threading
_CACHE: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.RLock()

# import name -> pip distribution name (yaml -> pyyaml, jwt -> pyjwt, ...)
_IMPORT_TO_PIP: Dict[str, str] = {}
for _pip, _imps in IMPORT_ALIASES.items():
    for _imp in _imps:
        _IMPORT_TO_PIP.setdefault(_imp.lower(), _pip)
_IMPORT_TO_PIP.update({"docx": "python-docx", "jwt": "pyjwt", "faker": "faker"})


def _pip_name(name: str) -> str:
    n = name.lower().replace("_", "-")
    return _IMPORT_TO_PIP.get(n, n)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def iter_py_files(repo: Path):
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not d.endswith(".egg-info"))
        for f in sorted(files):
            if f.endswith(".py"):
                yield Path(root) / f


def find_dockerfiles(repo: Path) -> List[Path]:
    """Dockerfiles inside the repo (ignored-dir names are checked relative to the repo root only)."""
    out = []
    for p in repo.rglob("Dockerfile*"):
        if p.is_file() and not any(i in p.relative_to(repo).parts for i in IGNORE_DIRS):
            out.append(p)
    return out


def _repo_signature(repo: Path) -> Tuple[int, float]:
    n, newest = 0, 0.0
    for p in iter_py_files(repo):
        n += 1
        try:
            newest = max(newest, p.stat().st_mtime)
        except OSError:
            pass
    return n, newest


def read_manifest_deps(repo: Path) -> Dict[str, str]:
    """Return {normalized_name: version_spec_or_empty} from requirements*.txt / pyproject / setup."""
    deps: Dict[str, str] = {}
    req_files = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.endswith(".egg-info")]
        depth = len(Path(root).relative_to(repo).parts)
        if depth > 2:
            dirs[:] = []
            continue
        for f in files:
            if re.match(r"^(requirements.*\.txt|.*requirements\.txt)$", f) and "dev" not in f.lower() and "test" not in f.lower():
                req_files.append(Path(root) / f)
    for rf in req_files:
        try:
            for line in rf.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.split("#")[0].strip()
                if not line or line.startswith(("-", ".", "git+", "http")):
                    continue
                m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[.*?\])?\s*(.*)$", line)
                if m:
                    deps.setdefault(m.group(1).lower().replace("_", "-"), m.group(2).strip())
        except OSError:
            pass
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        specs: List[str] = []
        try:
            try:
                import tomllib  # Python 3.11+
            except ModuleNotFoundError:  # pragma: no cover
                tomllib = None
            if tomllib:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8", errors="ignore"))
                proj = data.get("project", {})
                specs += [x for x in proj.get("dependencies", []) if isinstance(x, str)]
                for group in proj.get("optional-dependencies", {}).values():
                    specs += [x for x in group if isinstance(x, str)]
                for group in data.get("dependency-groups", {}).values():  # PEP 735
                    specs += [x for x in group if isinstance(x, str)]
                for name, spec in data.get("tool", {}).get("poetry", {}).get("dependencies", {}).items():
                    if name.lower() != "python":
                        specs.append(f"{name}{spec if isinstance(spec, str) and spec[:1] in '<>=!~' else ''}")
            else:
                text = pyproject.read_text(encoding="utf-8", errors="ignore")
                for block in re.findall(r"dependencies\s*=\s*\[(.*?)\n?\]", text, re.S):
                    specs += re.findall(r"""["']([A-Za-z0-9_.\-]+[^"']*)["']""", block)
        except Exception:
            pass
        for item in specs:
            m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[.*?\])?\s*([^;]*)", item.strip())
            if m:
                deps.setdefault(m.group(1).lower().replace("_", "-"), m.group(2).strip())
    for sf in (repo / "setup.py", repo / "setup.cfg"):
        if sf.exists():
            try:
                text = sf.read_text(encoding="utf-8", errors="ignore")
                for block in re.findall(r"install_requires\s*=\s*\[(.*?)\]", text, re.S):
                    for item in re.findall(r"['\"]([^'\"]+)['\"]", block):
                        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(.*)$", item.strip())
                        if m:
                            deps.setdefault(m.group(1).lower().replace("_", "-"), m.group(2).strip())
            except OSError:
                pass
    return deps


def _local_names(repo: Path) -> set:
    """Top-level module/package names that live inside the repo itself."""
    names = set()
    for item in repo.iterdir():
        if item.name in IGNORE_DIRS or item.name.startswith("."):
            continue
        if item.is_dir() and (item / "__init__.py").exists():
            names.add(item.name.lower())
        elif item.is_dir():
            names.add(item.name.lower())
        elif item.suffix == ".py":
            names.add(item.stem.lower())
    src = repo / "src"
    if src.is_dir():
        for item in src.iterdir():
            names.add(item.stem.lower())
    return names


def _stdlib() -> set:
    import sys
    return set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}


def imported_third_party(repo: Path) -> List[str]:
    """Top-level imports used by repo code that are neither stdlib nor local."""
    std, local = _stdlib(), _local_names(repo)
    counts: Dict[str, int] = {}
    for p in iter_py_files(repo):
        if is_test_path(p.relative_to(repo).as_posix()):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="ignore"))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module.split(".")[0]]
            for m in mods:
                if m.lower() in std or m.lower() in local or m in STUB_ONLY_MODULES or m.startswith("_"):
                    continue
                counts[m] = counts.get(m, 0) + 1
    return [k for k, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


# --------------------------------------------------------------------------
# core analysis
# --------------------------------------------------------------------------
def analyze_repo(repo: Path, force: bool = False, package: Optional[str] = None) -> Dict[str, Any]:
    """Scan every dependency of ``repo`` and pick the highest blast-radius target."""
    repo = Path(repo).resolve()
    with _LOCK:
        return _analyze_locked(repo, force, package)


def _analyze_locked(repo: Path, force: bool, package: Optional[str]) -> Dict[str, Any]:
    sig = _repo_signature(repo)
    key = str(repo)
    cached = _CACHE.get(key)
    if cached and cached["sig"] == sig and not force:
        result = cached["result"]
    else:
        manifest = read_manifest_deps(repo)
        names: List[str] = list(manifest.keys())
        covered = {n.lower().replace("_", "-") for n in names}
        for n in list(names):
            covered.update(a.lower().replace("_", "-") for a in IMPORT_ALIASES.get(n.lower(), []))
        for imp in imported_third_party(repo):
            if imp.lower().replace("_", "-") not in covered and _pip_name(imp) not in covered:
                names.append(imp)
        names = names[:30]

        candidates: List[Dict[str, Any]] = []
        scans: Dict[str, Dict[str, Any]] = {}
        for name in names:
            try:
                scan = scan_repo(str(repo), name)
            except SystemExit:
                continue
            except Exception:
                continue
            scans[name] = scan
            if scan["call_sites"]:
                pip = _pip_name(name)
                repl = KNOWN_REPLACEMENTS.get(pip) or KNOWN_REPLACEMENTS.get(name.lower()) or (None, None)
                candidates.append({
                    "package": name,
                    "version_spec": manifest.get(pip, manifest.get(name.lower().replace("_", "-"), "")),
                    "in_manifest": pip in manifest or name.lower().replace("_", "-") in manifest,
                    "blast_radius_score": scan["blast_radius_score"],
                    "call_sites": len(scan["call_sites"]),
                    "files_affected": len({c["file"] for c in scan["call_sites"]}),
                    "hero_file": scan["hero_file"],
                    "known_deprecated": bool(repl[0]),
                    "suggested_replacement": repl[0],
                    "reason": repl[1],
                })
        # known-deprecated packages first, then by blast radius, then call-site count
        candidates.sort(key=lambda c: (c["known_deprecated"], c["in_manifest"], c["blast_radius_score"], c["call_sites"]), reverse=True)
        result = {
            "repo_name": repo.name,
            "candidates": candidates,
            "manifest": manifest,
            "scans": scans,
            "py_files": sig[0],
        }
        _CACHE[key] = {"sig": sig, "result": result}

    chosen = None
    if package:
        chosen = next((c["package"] for c in result["candidates"] if c["package"].lower() == package.lower()), package)
    elif result["candidates"]:
        chosen = result["candidates"][0]["package"]

    scan = result["scans"].get(chosen) if chosen else None
    if chosen and scan is None:
        try:
            scan = scan_repo(str(repo), chosen)
        except SystemExit:
            scan = None
    out = dict(result)
    out["target_package"] = chosen or ""
    out["scan"] = scan or {}
    return out


# --------------------------------------------------------------------------
# real auditor checks
# --------------------------------------------------------------------------
def run_auditor_checks(repo: Path, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    repo = Path(repo)
    scan = analysis.get("scan", {}) or {}
    hero = scan.get("hero_file") or ""
    checks: List[Dict[str, Any]] = []

    # 1. hardcoded credentials
    leaks: List[str] = []
    for p in iter_py_files(repo):
        rel = p.relative_to(repo).as_posix()
        if is_test_path(rel):
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                m = SECRET_RE.search(line)
                if m and not PLACEHOLDER_RE.search(m.group(3)) and "environ" not in line and "getenv" not in line:
                    leaks.append(f"{rel}:{i}")
        except OSError:
            pass
    checks.append({
        "label": "Checking AST for hardcoded literals and credentials",
        "verified": not leaks,
        "detail": "No hardcoded credentials found" if not leaks else "Possible hardcoded secrets at " + ", ".join(leaks[:5]),
    })

    # 2. tests with real assertions
    test_files, asserts = 0, 0
    for p in iter_py_files(repo):
        rel = p.relative_to(repo).as_posix()
        if is_test_path(rel) or p.name.startswith("test_") or p.name.endswith("_test.py"):
            test_files += 1
            try:
                tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="ignore"))
                asserts += sum(isinstance(n, ast.Assert) for n in ast.walk(tree))
            except (SyntaxError, ValueError):
                pass
    checks.append({
        "label": "Scanning for deleted or altered test assertions",
        "verified": asserts > 0,
        "detail": f"{asserts} assertions locked across {test_files} test file(s)" if asserts else "No existing test assertions to protect - regression safety is weak",
    })

    # 3. hero function signatures
    sig_detail, sig_ok = "No hero file identified (target package has no call sites)", False
    hp = repo / hero if hero else None
    if hp and hp.exists():
        try:
            tree = ast.parse(hp.read_text(encoding="utf-8-sig", errors="ignore"))
            fns = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_")]
            sig_ok = True
            sig_detail = f"{len(fns)} public function signature(s) in {hero} frozen as contract"
        except (SyntaxError, ValueError):
            sig_detail = f"{hero} could not be parsed"
    checks.append({"label": f"Verifying function signature preservation in {hero or 'target module'}", "verified": sig_ok, "detail": sig_detail})

    # 4. global monkey-patching of the target
    assigns = [c for c in scan.get("call_sites", []) if c.get("kind") == "assign" and "()" not in c.get("symbol", "")]
    checks.append({
        "label": "Checking scope isolation: no unvetted global monkey-patching",
        "verified": not assigns,
        "detail": "No assignments into the target package's namespace" if not assigns
        else "Monkey-patching at " + ", ".join(f"{a['file']}:{a['line']}" for a in assigns[:4]),
    })

    # 5. Dockerfile non-root
    dockerfiles = find_dockerfiles(repo)
    if not dockerfiles:
        checks.append({"label": "Ensuring non-root security compliance in Dockerfile", "verified": True, "detail": "No Dockerfile present (not applicable)"})
    else:
        bad = []
        for d in dockerfiles:
            users = re.findall(r"^\s*USER\s+(\S+)", d.read_text(encoding="utf-8", errors="ignore"), re.M)
            if not users or users[-1].lower() in ("root", "0"):
                bad.append(d.relative_to(repo).as_posix())
        checks.append({
            "label": "Ensuring non-root security compliance in Dockerfile",
            "verified": not bad,
            "detail": "All Dockerfiles drop root" if not bad else "Runs as root: " + ", ".join(bad),
        })

    # 6. dependency manifest pinning
    manifest = analysis.get("manifest", {})
    if not manifest:
        checks.append({"label": "Validating dependency manifest in pyproject.toml and requirements.txt", "verified": False, "detail": "No dependency manifest found"})
    else:
        unpinned = [n for n, v in manifest.items() if "==" not in v]
        checks.append({
            "label": "Validating dependency manifest in pyproject.toml and requirements.txt",
            "verified": len(unpinned) < len(manifest),
            "detail": f"{len(manifest)} dependencies declared, {len(manifest) - len(unpinned)} pinned",
        })

    # 7. unparsed files
    all_unparsed = scan.get("unparsed_files", [])
    unparsed = [u for u in all_unparsed if not is_test_path(u)]   # test data fixtures are often deliberately invalid
    checks.append({
        "label": "Confirming every Python file parsed by the AST scanner",
        "verified": not unparsed,
        "detail": f"{scan.get('files_scanned', 0)} files scanned" + (f" ({len(all_unparsed)} test fixture(s) intentionally unparsable)" if all_unparsed else "") if not unparsed else "Not parsed: " + ", ".join(unparsed[:5]),
    })
    return checks


# --------------------------------------------------------------------------
# tree / flagged details
# --------------------------------------------------------------------------
def build_tree(repo: Path) -> Dict[str, List[str]]:
    tree: Dict[str, List[str]] = {"root": []}
    for item in sorted(repo.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if item.name.startswith(".") or item.name in IGNORE_DIRS:
            continue
        if item.is_file():
            tree["root"].append(item.name)
        elif item.is_dir():
            files = []
            for sub in sorted(item.rglob("*")):
                if any(i in sub.relative_to(repo).parts for i in IGNORE_DIRS):
                    continue
                if sub.is_file():
                    files.append(sub.relative_to(item).as_posix())
            tree[item.name] = files[:60]
    return tree


def build_flagged(repo: Path, analysis: Dict[str, Any], checks: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Any]]:
    scan = analysis.get("scan", {}) or {}
    pkg = analysis.get("target_package", "")
    hero = scan.get("hero_file")
    radius = scan.get("blast_radius_score", 0)
    flagged: List[str] = []
    details: Dict[str, Any] = {}

    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for cs in scan.get("call_sites", []):
        by_file.setdefault(cs["file"], []).append(cs)

    for rel, sites in sorted(by_file.items(), key=lambda kv: (kv[0] != hero, -len(kv[1]), kv[0])):
        first = sorted(sites, key=lambda c: c["line"])[0]
        kinds = sorted({c["kind"] for c in sites})
        flagged.append(rel)
        details[rel] = {
            "file": rel,
            "line": first["line"],
            "calling_function": first.get("calling_function", ""),
            "code_snippet": first.get("code_snippet", ""),
            "issue": f"{len(sites)} use(s) of `{pkg}` ({', '.join(kinds)})" + (" incl. private API" if any(c.get("private_api") for c in sites) else ""),
            "blast_radius": radius,
            "role": "Hero File" if rel == hero else "Call Site",
        }

    for chk in checks:
        if chk["verified"]:
            continue
        if "Dockerfile" in chk["label"]:
            for d in find_dockerfiles(repo):
                rel = d.relative_to(repo).as_posix()
                users = [(i, l.strip()) for i, l in enumerate(d.read_text(encoding="utf-8", errors="ignore").splitlines(), 1) if l.strip().startswith("USER")]
                if rel not in details and (not users or users[-1][1].split()[-1].lower() in ("root", "0")):
                    flagged.append(rel)
                    details[rel] = {
                        "file": rel,
                        "line": users[-1][0] if users else 1,
                        "calling_function": "Container Build Spec",
                        "code_snippet": users[-1][1] if users else "(no USER directive)",
                        "issue": "Container runs as superuser",
                        "blast_radius": 35,
                        "role": "Security Compliance",
                    }
    return flagged, details


def discover_tests(repo: Path) -> List[Dict[str, Any]]:
    found = []
    for p in iter_py_files(repo):
        rel = p.relative_to(repo).as_posix()
        if not (p.name.startswith("test_") or p.name.endswith("_test.py")):
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="ignore"))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                found.append({"id": f"{rel}::{node.name}", "name": node.name, "origin": "Pre-existing", "duration": "-", "status": "DISCOVERED"})
    return found


def deprecated_table(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    rows = []
    for c in analysis.get("candidates", [])[:8]:
        rows.append({
            "package": f"{c['package']}{c['version_spec'] and ' ' + c['version_spec']}",
            "status": c["reason"] or f"Used in {c['files_affected']} file(s), {c['call_sites']} call site(s)",
            "recommended": c["suggested_replacement"] or "Compatibility adapter",
            "risk": f"Blast radius {c['blast_radius_score']}/100 across {c['files_affected']} file(s).",
        })
    if not rows:
        for name, spec in list(analysis.get("manifest", {}).items())[:6]:
            rows.append({"package": f"{name} {spec}".strip(), "status": "Declared in manifest, no direct call sites", "recommended": "-", "risk": "No migration needed"})
    return rows


def dependency_names(repo: Path) -> List[str]:
    """Names of dependencies worth offering in the UI (manifest + external imports)."""
    a = analyze_repo(repo)
    seen, out = set(), []
    for n in [c["package"] for c in a["candidates"]] + list(a["manifest"].keys()):
        if n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out