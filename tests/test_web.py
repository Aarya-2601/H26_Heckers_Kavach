"""Unit tests for Kavach Flask web application and API endpoints."""

import json
from pathlib import Path

import pytest

from web.server import app, get_active_repo, set_active_repo

client = app.test_client()


@pytest.fixture
def sample_repo(tmp_path):
    """Create a small throwaway repository, make it active, and restore the previous one after."""
    repo = tmp_path / "sample_project"
    repo.mkdir()
    (repo / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    pkg = repo / "sample_pkg"
    pkg.mkdir()
    (pkg / "checker.py").write_text(
        "import requests\n\n\ndef fetch(url):\n    return requests.get(url)\n",
        encoding="utf-8",
    )
    previous = get_active_repo()
    set_active_repo(repo)
    try:
        yield repo
    finally:
        set_active_repo(previous)


def test_index_route():
    """Verify root / serves the HTML frontend with Kavach branding."""
    response = client.get("/")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Kavach" in text
    assert "canvas" in text.lower()
    assert "chatbot-panel" in text


def test_api_status_endpoint(sample_repo):
    """Verify /api/status returns valid system telemetry."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["project_name"] == "Kavach"
    assert data["target_repo"] == str(sample_repo.resolve())
    assert data["repo_name"] == sample_repo.name
    assert "ast_output" in data
    assert "history" in data
    assert "checks" in data
    assert len(data["checks"]) > 0
    assert "red_team_suite" in data


def test_api_tests_endpoint(sample_repo):
    """Verify /api/tests returns pre-existing and Red Team adversarial edge cases."""
    response = client.get("/api/tests")
    assert response.status_code == 200
    data = response.get_json()
    assert "pre_existing" in data
    assert "set_a_tests" in data
    assert "set_b_edge_cases" in data
    assert isinstance(data["set_a_tests"], list)
    assert isinstance(data["set_b_edge_cases"], list)
    assert data["oracle_verified"] == bool(data["set_a_tests"] or data["set_b_edge_cases"])


def test_api_tree_endpoint(sample_repo):
    """Verify /api/tree returns repository tree with flagged files."""
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.get_json()
    assert data["repo_name"] == sample_repo.name
    assert "tree" in data
    assert "flagged_files" in data
    assert isinstance(data["flagged_files"], list)


def test_api_capsule_endpoint():
    """Verify /api/capsule returns CAPSULE.md artifact."""
    response = client.get("/api/capsule")
    assert response.status_code == 200
    data = response.get_json()
    assert "content" in data
    assert "filename" in data
    assert "CAPSULE.md" in data["filename"]


def test_api_chat_general():
    """Verify /api/chat answers general inquiries with AI formatting."""
    payload = {"message": "Hello, how does Kavach work?", "voice_used": False}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["sender"] == "ai"
    assert "reply" in data
    assert "solution" in data
    assert "🤖" not in data["reply"]
    assert "🤖" not in (data["solution"] or "")


def test_api_chat_tree_and_audit():
    """Verify /api/chat specifically recognizes AST and Tree queries."""
    payload = {"message": "Show flagged files and AST blast radius", "voice_used": False}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["reasoning_steps"]) > 0
    assert "AST" in data["reply"] or "flagged" in data["reply"].lower()


def test_api_chat_voice_flag():
    """Verify voice_used flag is preserved and handled cleanly."""
    payload = {"message": "Run auto-heal loop now", "voice_used": True}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["sender"] == "ai"
    assert "auto-heal" in data["reply"].lower() or "heal" in data["reply"].lower()


def test_api_run_search():
    """Verify /api/run-search executes and returns status."""
    response = client.post("/api/run-search")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] in ("simulated_success", "success")
    assert "winning_node" in data


def test_api_active_repo_endpoint():
    """Verify /api/active-repo returns active repository information."""
    response = client.get("/api/active-repo")
    assert response.status_code == 200
    data = response.get_json()
    assert "repo_path" in data
    assert "repo_name" in data
    assert "detected_dependencies" in data
    assert isinstance(data["detected_dependencies"], list)


def test_api_select_repo_dynamic(tmp_path):
    """Verify /api/select-repo dynamically switches repo and detects dependencies."""
    # Create a dummy arbitrary repository
    dummy_repo = tmp_path / "dummy_project"
    dummy_repo.mkdir()
    req = dummy_repo / "requirements.txt"
    req.write_text("requests==2.31.0\npydantic>=2.0\n", encoding="utf-8")
    src = dummy_repo / "src"
    src.mkdir()
    (src / "app.py").write_text("import requests\n\ndef main(): pass\n", encoding="utf-8")

    previous_repo = get_active_repo()

    # Select repo
    res = client.post("/api/select-repo", json={"repo_path": str(dummy_repo)})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["repo_name"] == "dummy_project"
    assert "requests" in data["detected_dependencies"]

    # Test /api/tree on selected repo
    tree_res = client.get(f"/api/tree?repo={dummy_repo}")
    assert tree_res.status_code == 200
    tree_data = tree_res.get_json()
    assert tree_data["repo_name"] == "dummy_project"
    assert "src" in tree_data["tree"]

    # Restore the previously active repo
    set_active_repo(previous_repo)


def test_api_select_repo_invalid():
    """Verify /api/select-repo gracefully handles nonexistent paths."""
    res = client.post("/api/select-repo", json={"repo_path": "nonexistent_directory_xyz_123"})
    assert res.status_code == 404
    data = res.get_json()
    assert data["status"] == "error"