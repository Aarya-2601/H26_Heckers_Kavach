"""Unit tests for Kavach Flask web application and API endpoints."""

import json
from pathlib import Path
from web.server import app

client = app.test_client()


def test_index_route():
    """Verify root / serves the HTML frontend with Kavach branding."""
    response = client.get("/")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Kavach" in text
    assert "canvas" in text.lower()
    assert "chatbot-panel" in text


def test_api_status_endpoint():
    """Verify /api/status returns valid system telemetry."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["project_name"] == "Kavach"
    assert "LinkWatch" in data["target_repo"]
    assert "ast_output" in data
    assert "history" in data
    assert "checks" in data
    assert len(data["checks"]) > 0
    assert "red_team_suite" in data


def test_api_tests_endpoint():
    """Verify /api/tests returns pre-existing and Red Team adversarial edge cases."""
    response = client.get("/api/tests")
    assert response.status_code == 200
    data = response.get_json()
    assert "pre_existing" in data
    assert "set_a_tests" in data
    assert "set_b_edge_cases" in data
    assert data["oracle_verified"] is True
    assert len(data["set_b_edge_cases"]) > 0


def test_api_tree_endpoint():
    """Verify /api/tree returns repository tree with flagged files."""
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.get_json()
    assert data["repo_name"] == "LinkWatch"
    assert "tree" in data
    assert "flagged_files" in data
    assert len(data["flagged_files"]) > 0
    assert any("checker.py" in f or "http_patch.py" in f for f in data["flagged_files"])


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


def test_api_active_repo():
    """Verify /api/active-repo returns repository name and candidate dependencies."""
    response = client.get("/api/active-repo")
    assert response.status_code == 200
    data = response.get_json()
    assert "repo_name" in data
    assert "target_package" in data
    assert "available_dependencies" in data


def test_api_select_repo():
    """Verify /api/select-repo can select a valid repository path."""
    response = client.post("/api/select-repo", json={"repo": "dataset/LinkWatch"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "LinkWatch" in data["repo_name"]
