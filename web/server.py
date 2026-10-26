"""Kavach Web Dashboard Server.

Provides live API endpoints and serves the static frontend:
- GET /api/status: Returns live contracts (run_result.json, ast_output.json, gemma_output.json)
- GET /api/tree: Returns repository tree structure and flagged files
- GET /api/tests: Returns test suites (pre-existing, Set A gates, Set B edge cases)
- GET /api/capsule: Returns raw/rendered CAPSULE.md artifact
- GET /api/active-repo: Returns currently active repository info
- POST /api/select-repo: Dynamically switches the active repository
- POST /api/chat: Interactive AI companion endpoint with Gemma reasoning & AST advice
- POST /api/run-search: Triggers live search loop execution
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Compatibility shim for MarkupSafe / Jinja2 soft_unicode
import markupsafe
if not hasattr(markupsafe, "soft_unicode"):
    markupsafe.soft_unicode = str

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web import analysis as kv_analysis

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
CORS(app)

def _default_repo_path() -> Path:
    """TARGET_REPO env var, else the first repo folder under dataset/, else dataset/ itself."""
    env_repo = os.environ.get("TARGET_REPO")
    if env_repo:
        return Path(env_repo).resolve()
    dataset_dir = BASE_DIR / "dataset"
    if dataset_dir.is_dir():
        for child in sorted(dataset_dir.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                return child.resolve()
    return dataset_dir.resolve()


# Active repository state (any repo can be selected at runtime via /api/select-repo)
_ACTIVE_REPO_PATH: Path = _default_repo_path()


def get_active_repo() -> Path:
    """Return the currently selected repository Path."""
    return _ACTIVE_REPO_PATH


def _is_git_url(value: str) -> bool:
    """True for http(s)/git URLs or git@host:owner/repo style remotes."""
    v = value.strip()
    return bool(re.match(r"^(https?://|git@|git://|ssh://)", v))


def clone_repo(url: str) -> Path:
    """Fetch a GitHub repo as a zip over HTTPS (no git needed) and extract it to .cloned_repos/."""
    import io
    import shutil
    import zipfile
    import requests

    url = url.strip().rstrip("/")
    m = re.match(r"^https?://github\.com/([^/]+)/([^/#?]+?)(?:\.git)?(?:/tree/([^/#?]+))?(?:[/#?].*)?$", url)
    if not m:
        raise ValueError("Only GitHub URLs are supported, e.g. https://github.com/owner/repo")
    owner, repo, branch = m.group(1), m.group(2), m.group(3)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{owner}_{repo}")
    dest = BASE_DIR / ".cloned_repos" / safe
    if dest.exists() and any(dest.iterdir()):
        return dest

    refs = [branch] if branch else ["HEAD", "main", "master"]
    data = None
    for ref in refs:
        r = requests.get(f"https://codeload.github.com/{owner}/{repo}/zip/{ref}", timeout=60)
        if r.status_code == 200:
            data = r.content
            break
    if data is None:
        raise ValueError("Could not download repo (private, wrong URL, or no network)")

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        root = zf.namelist()[0].split("/")[0]
        for member in zf.infolist():
            rel = member.filename[len(root):].lstrip("/")
            if not rel or member.is_dir():
                continue
            target = (dest / rel).resolve()
            if dest.resolve() not in target.parents:  # zip-slip guard
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(member))
    return dest


def set_active_repo(repo_path: str | Path) -> Path:
    """Set the active repository path if it exists."""
    global _ACTIVE_REPO_PATH
    if _is_git_url(str(repo_path)):
        repo_path = clone_repo(str(repo_path))
    p = Path(repo_path).resolve()
    if not p.exists() or not p.is_dir():
        # Check relative to BASE_DIR
        alt = (BASE_DIR / repo_path).resolve()
        if alt.exists() and alt.is_dir():
            p = alt
        else:
            raise ValueError(f"Repository directory does not exist: {repo_path}")
    _ACTIVE_REPO_PATH = p
    return _ACTIVE_REPO_PATH


def _load_json_safe(file_path: Path) -> Dict[str, Any]:
    if file_path.exists():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _contracts_for(repo_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load contract JSONs, but only if they were produced for this repository."""
    ast_out = _load_json_safe(BASE_DIR / "contracts" / "ast_output.json")
    gemma = _load_json_safe(BASE_DIR / "contracts" / "gemma_output.json")
    run = _load_json_safe(BASE_DIR / "contracts" / "run_result.json")
    recorded = ast_out.get("repo_path")
    # Contracts only apply to the repository they were recorded for
    match = bool(recorded) and Path(recorded).resolve() == Path(repo_path).resolve()
    if not match:
        return {"ast": {}, "gemma": {}, "run": {}}
    return {"ast": ast_out, "gemma": gemma, "run": run}


def scan_repo_tests(repo_path: Path) -> List[Dict[str, Any]]:
    """Discover real tests from the target repo's test files (AST-based)."""
    return kv_analysis.discover_tests(repo_path)


REWARD_WEIGHTS = [
    {"component": "R_extrinsic (Goal)", "weight": "+100 pts", "condition": "exit_code == 0 (All tests pass)", "desc": "Verified software correctness."},
    {"component": "R_curiosity (Bonus)", "weight": "+30 pts", "condition": "New unique error signature", "desc": "Rewards exploring diverse execution paths."},
    {"component": "P_latency (Penalty)", "weight": "-10 pts", "condition": "execution_time_ms > baseline_time_ms", "desc": "Disincentivizes performance degradation."},
    {"component": "P_bloat (Penalty)", "weight": "-1 pt / line", "condition": "Added lines in diff patch", "desc": "Promotes minimal compatibility shims."},
    {"component": "P_anti_cheat (Penalty)", "weight": "-9999 pts", "condition": "Tampering with tests/assertions", "desc": "Immediate catastrophic disqualification."},
]
ROLES = [
    {"role": "Person 1: The Referee", "lead": "Aarya", "dir": "engine/", "desc": "Lead Search & Policy Architect (MCTS, Sandbox, Rewards)"},
    {"role": "Person 2: The Detective", "lead": "Rushil", "dir": "analyzer/", "desc": "AST & Blast Radius Engineer (Scanner, Call Sites, Auditor)"},
    {"role": "Person 3: The Whisperer", "lead": "Param", "dir": "dependency_whisperer/", "desc": "Gemma 4 Cognitive Engine (Red/Blue Teams, CoT, Patches)"},
    {"role": "Person 4: The Presenter", "lead": "Omisha", "dir": "src/ & web/", "desc": "UI, Visualizer, CAPSULE & Web Platform"},
]


def scan_repo_tree(repo_path: Path) -> Dict[str, Any]:
    """Real tree, flagged files and call-site details for ANY repository."""
    analysis = kv_analysis.analyze_repo(repo_path)
    checks = kv_analysis.run_auditor_checks(repo_path, analysis)
    flagged, details = kv_analysis.build_flagged(repo_path, analysis, checks)
    tree = kv_analysis.build_tree(repo_path)
    return {
        "repo_name": repo_path.name,
        "root": str(repo_path),
        "target_package": analysis.get("target_package", ""),
        "candidates": analysis.get("candidates", []),
        "flagged_files": flagged,
        "tree": tree,
        "flagged_details": details,
        "structure": tree,
        "deprecated_packages": kv_analysis.deprecated_table(analysis),
        "reward_weights": REWARD_WEIGHTS,
        "roles": ROLES,
    }


@app.route("/api/active-repo", methods=["GET"])
def get_active_repo_endpoint():
    """Return currently active repository info and auto-detected dependencies."""
    repo = get_active_repo()
    deps = kv_analysis.dependency_names(repo) if repo.exists() else []
    return jsonify({
        "repo_path": str(repo),
        "repo_name": repo.name,
        "detected_dependencies": deps,
    })


@app.route("/api/select-repo", methods=["POST"])
def select_repo_endpoint():
    """Switch the active repository dynamically at runtime."""
    data = request.get_json(silent=True) or {}
    repo_path = data.get("repo_path") or data.get("repo")
    if not repo_path:
        return jsonify({"status": "error", "message": "Missing 'repo_path' in request body"}), 400

    try:
        new_repo = set_active_repo(repo_path)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404

    deps = kv_analysis.dependency_names(new_repo)

    return jsonify({
        "status": "success",
        "repo_path": str(new_repo),
        "repo_name": new_repo.name,
        "detected_dependencies": deps,
    })


@app.route("/api/status", methods=["GET"])
def get_status():
    """Return live telemetry computed from the active repository."""
    target_repo_arg = request.args.get("repo")
    repo_path = Path(target_repo_arg).resolve() if target_repo_arg else get_active_repo()

    c = _contracts_for(repo_path)
    run_result, gemma_output = c["run"], c["gemma"]
    # Analysis for this repo (the package the last run used, otherwise the riskiest one)
    analysis = kv_analysis.analyze_repo(repo_path, package=c["ast"].get("target_package") or None)
    scan = analysis.get("scan", {}) or {}
    checks = kv_analysis.run_auditor_checks(repo_path, analysis)
    flagged_files, _ = kv_analysis.build_flagged(repo_path, analysis, checks)

    target_pkg = analysis.get("target_package", "")
    cand = next((x for x in analysis["candidates"] if x["package"] == target_pkg), {})
    replacement = gemma_output.get("replacement_candidate") or cand.get("suggested_replacement") or (f"{target_pkg}-modern" if target_pkg else "")

    history = run_result.get("history", [])
    if not history:
        history = [{
            "node_id": "node_0", "parent_id": None,
            "action_name": f"Baseline ({target_pkg or 'no target'})",
            "status": "BASELINE", "reward_score": 0, "execution_time_ms": 0,
        }]

    ast_output = {
        "target_package": target_pkg,
        "blast_radius_score": scan.get("blast_radius_score", 0),
        "hero_file": scan.get("hero_file") or "",
        "vulnerabilities_count": len(flagged_files),
        "flagged_files": flagged_files,
        "call_sites": scan.get("call_sites", []),
        "files_scanned": scan.get("files_scanned", 0),
        "candidates": analysis.get("candidates", []),
    }
    return jsonify({
        "project_name": "Kavach",
        "target_repo": str(repo_path),
        "repo_name": repo_path.name,
        "search_run": bool(run_result),
        "ast_output": ast_output,
        "gemma_output": gemma_output or {
            "replacement_candidate": replacement,
            "migration_strategy": f"Run the auto-heal search to generate a migration for {target_pkg}" if target_pkg else "No migratable dependency detected",
        },
        "history": history,
        "checks": checks,
        "search_loop": {
            "winning_node": run_result.get("winning_node", {}),
            "total_nodes_explored": run_result.get("total_nodes_explored", len(history)),
            "history": history,
            "mermaid_dag": run_result.get("mermaid_dag", ""),
        },
        "auditor_checklist": checks,
        "red_team_suite": {
            "set_a_tests": gemma_output.get("set_a_tests", []),
            "set_b_tests": gemma_output.get("set_b_tests", []),
            "edge_cases_count": gemma_output.get("edge_cases_count", len(gemma_output.get("set_b_tests", []))),
            "full_pytest_file_content": gemma_output.get("full_pytest_file_content", ""),
        },
    })


@app.route("/api/tests", methods=["GET"])
def get_tests():
    """Return all test suites: pre-existing, Set A compatibility gates, and Set B adversarial edge cases."""
    target_repo_arg = request.args.get("repo")
    repo_path = Path(target_repo_arg).resolve() if target_repo_arg else get_active_repo()
    gemma_output = _contracts_for(repo_path)["gemma"]

    pre_existing = scan_repo_tests(repo_path)
    set_a = gemma_output.get("set_a_tests", [])
    set_b = gemma_output.get("set_b_tests", [])

    run = _contracts_for(repo_path)["run"]
    hist = run.get("history", [])
    base = next((n for n in hist if n.get("node_id") == "node_0"), None)
    attempts = [n for n in hist if n.get("status") != "BASELINE"]
    best = max(attempts, key=lambda n: n.get("reward_score", 0), default=None)
    run_summary = {
        "has_run": bool(hist),
        "baseline_passed": bool(base and (base.get("run_result") or {}).get("passed")),
        "baseline_ms": (base.get("run_result") or {}).get("execution_time_ms", 0) if base else 0,
        "winner_status": (best or base or {}).get("status", "UNKNOWN"),
        "winner_ms": ((best or {}).get("run_result") or {}).get("execution_time_ms", 0),
    }
    return jsonify({
        "run_summary": run_summary,
        "pre_existing": pre_existing,
        "set_a_tests": set_a,
        "set_b_edge_cases": set_b,
        "total_count": len(pre_existing) + len(set_a) + len(set_b),
        "oracle_verified": bool(set_a or set_b),
        "pytest_content": gemma_output.get("full_pytest_file_content", "")
    })


@app.route("/api/tree", methods=["GET"])
def get_tree():
    """Return repository structure, flagged files and AST details."""
    target_repo_arg = request.args.get("repo")
    repo_path = Path(target_repo_arg).resolve() if target_repo_arg else get_active_repo()
    return jsonify(scan_repo_tree(repo_path))


@app.route("/api/capsule", methods=["GET"])
def get_capsule():
    """Return the contents of CAPSULE.md."""
    capsule_file = BASE_DIR / "CAPSULE.md"
    repo = get_active_repo()
    if not _contracts_for(repo)["run"]:
        content = f"# CAPSULE\n\nNo Dependency Exit Capsule has been generated for `{repo.name}` yet.\nRun the Auto-Heal search on the Tree tab to produce one."
    elif capsule_file.exists():
        content = capsule_file.read_text(encoding="utf-8")
    else:
        from src.capsule import generate_capsule_markdown
        content = generate_capsule_markdown()
    return jsonify({"content": content, "filename": "CAPSULE.md"})


@app.route("/api/run-search", methods=["POST"])
def run_search_endpoint():
    """Run the real pipeline (AST scan -> Red/Blue team -> sandbox search -> CAPSULE) on the active repo."""
    data = request.get_json(silent=True) or {}
    target_pkg = data.get("package") or data.get("dependency")
    repo_path = data.get("repo") or data.get("repo_path") or str(get_active_repo())
    backend = data.get("backend") or "auto"

    if not target_pkg:
        target_pkg = kv_analysis.analyze_repo(Path(repo_path)).get("target_package") or None
    if not target_pkg:
        return jsonify({"status": "error", "message": "No third-party dependency with call sites was found in this repository."}), 422

    import contextlib, io, traceback
    cwd = os.getcwd()
    buf = io.StringIO()
    try:
        os.chdir(BASE_DIR)
        from main import run_pipeline
        with contextlib.redirect_stdout(buf):
            run_pipeline(repo_path=str(repo_path), target_pkg=target_pkg, interactive=False, backend=backend)
    except BaseException as e:  # SystemExit from scan_repo included
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Pipeline failed: {e}"}), 500
    finally:
        os.chdir(cwd)

    c = _contracts_for(Path(repo_path))
    winning = c["run"].get("winning_node") or {}
    history = c["run"].get("history", [])
    passed = sum(1 for n in history if str(n.get("status", "")).upper() == "PASSED")
    return jsonify({
        "status": "success",
        "message": f"Auto-heal search completed for {target_pkg}.",
        "target_package": target_pkg,
        "winning_node": winning,
        "score": winning.get("reward_score", 0),
        "winning_status": winning.get("status", "UNKNOWN"),
        "nodes_explored": len(history),
        "nodes_passed": passed,
    })


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """Conversational companion grounded in the active repo's real analysis."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    msg = message.lower().strip()
    repo = get_active_repo()
    c = _contracts_for(repo)
    analysis = kv_analysis.analyze_repo(repo, package=c["ast"].get("target_package") or None)
    scan = analysis.get("scan", {}) or {}
    pkg = analysis.get("target_package") or "no dependency"
    hero = scan.get("hero_file") or "n/a"
    score = scan.get("blast_radius_score", 0)
    sites = scan.get("call_sites", [])
    cands = analysis.get("candidates", [])
    checks = kv_analysis.run_auditor_checks(repo, analysis)
    failing = [k for k in checks if not k["verified"]]

    if any(w in msg for w in ("replace", "migrate", "swap")) or (pkg.lower() in msg and pkg != "no dependency"):
        repl = (cands[0]["suggested_replacement"] if cands else None) or "a compatibility adapter"
        return jsonify({
            "reply": f"In {repo.name}, `{pkg}` has {len(sites)} call site(s) across {len({s_['file'] for s_ in sites})} file(s); the hero file is {hero}.",
            "solution": f"Plan: migrate {pkg} to {repo.name}-safe {repl} behind an isolated adapter that preserves existing signatures. Click 'Run Auto-Heal Search' to execute it in the sandbox.",
            "reasoning_steps": [f"{s_['file']}:{s_['line']} {s_.get('kind','')} -> {s_.get('symbol','')}" for s_ in sites[:4]] or ["No call sites found"],
            "sender": "ai",
        })
    if "blast" in msg or "score" in msg or "ast" in msg:
        return jsonify({
            "reply": f"AST blast radius for {pkg} in {repo.name} is {score}/100 ({len(sites)} call sites; files scanned: {scan.get('files_scanned', 0)}).",
            "solution": f"Hero file: {hero}.",
            "reasoning_steps": [f"{k['package']}: {k['blast_radius_score']}/100 ({k['call_sites']} sites)" for k in cands[:5]] or ["No dependency with call sites"],
            "sender": "ai",
        })
    if "audit" in msg or "check" in msg or "safe" in msg or "secur" in msg:
        return jsonify({
            "reply": f"{len(checks) - len(failing)}/{len(checks)} auditor checks pass for {repo.name}.",
            "solution": "; ".join(k["detail"] for k in failing) or "All deterministic checks are satisfied.",
            "reasoning_steps": [f"{'PASS' if k['verified'] else 'FAIL'}: {k['detail']}" for k in checks],
            "sender": "ai",
        })
    if "auto-heal" in msg or "dag" in msg or "tree" in msg or "why" in msg:
        hist = c["run"].get("history", [])
        if not hist:
            return jsonify({"reply": "No auto-heal search has been run for this repository yet.", "solution": "Click 'Run Auto-Heal Search' on the Tree tab.", "reasoning_steps": [], "sender": "ai"})
        return jsonify({
            "reply": "Search path: " + " -> ".join(f"{n.get('action_name')} [{n.get('status')}, {n.get('reward_score')}]" for n in hist),
            "solution": f"Winner: {(c['run'].get('winning_node') or {}).get('action_name', 'n/a')}",
            "reasoning_steps": [f"{n.get('node_id')}: {n.get('status')} in {n.get('execution_time_ms')}ms" for n in hist],
            "sender": "ai",
        })
    return jsonify({
        "reply": f"Monitoring {repo.name}: riskiest dependency is {pkg} (blast radius {score}/100, hero file {hero}).",
        "solution": "Ask about the blast radius, the audit, a migration plan, or the search tree.",
        "reasoning_steps": [f"{k['package']}: {k['blast_radius_score']}/100" for k in cands[:5]],
        "sender": "ai",
    })


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint confirming API status and model availability."""
    has_key = bool(
        os.environ.get("GEMMA_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    return jsonify({
        "status": "online",
        "service": "Kavach Dependency Resilience Platform",
        "version": "2.0.0",
        "hosted_api_configured": has_key,
        "default_backend": "hosted" if has_key else "mock",
    })


@app.route("/", methods=["GET"])
def serve_index():
    """Serve index.html directly from root route."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return "Frontend index.html not found.", 404
    return send_from_directory(str(STATIC_DIR), "index.html")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Kavach Dashboard Web Server")
    parser.add_argument("--repo", default=None, help="Target repository path (defaults to TARGET_REPO env var or first repo in dataset/)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    args = parser.parse_args()

    if args.repo:
        try:
            set_active_repo(args.repo)
        except Exception as e:
            print(f"[Warning] Could not set repository to {args.repo}: {e}")

    active_repo = get_active_repo()
    print(f"\n[Kavach] Starting Web Dashboard on http://{args.host}:{args.port}")
    print(f"   Active Repository: {active_repo} ({active_repo.name})")
    print(f"   API Endpoints:")
    print(f"   - GET  /api/health      - API health & backend diagnostic")
    print(f"   - GET  /api/status      - Live AST contracts & search loop state")
    print(f"   - GET  /api/tests       - Pre-existing + Red Team edge cases")
    print(f"   - GET  /api/tree        - AST repository visualizer")
    print(f"   - GET  /api/capsule     - CAPSULE.md artifact deliverable")
    print(f"   - GET  /api/active-repo - Current active repository info")
    print(f"   - POST /api/select-repo - Dynamically change target repository")
    print(f"   - POST /api/run-search  - Trigger dynamic search loop")
    print(f"   - POST /api/chat        - AI interactive companion\n")
    app.run(host=args.host, port=args.port, debug=args.debug)