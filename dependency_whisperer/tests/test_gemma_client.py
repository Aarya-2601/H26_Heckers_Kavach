"""
Tests for Gemma 4 Client & Deterministic Mock Engine.
"""

from dependency_whisperer.gemma_client import GemmaClient, GemmaModelMetadata
from dependency_whisperer.schemas import ReplacementRecommendation, TestSuitePlan


def test_client_initialization_defaults():
    client = GemmaClient(backend="mock")
    assert client.metadata.model_name == "gemma-4-it"
    assert client.backend == "mock"
    assert "Google Gemma" in client.metadata.applicable_terms


def test_json_extraction():
    client = GemmaClient(backend="mock")
    markdown_fence = "```json\n{\"key\": \"value\"}\n```"
    assert client.extract_json(markdown_fence) == "{\"key\": \"value\"}"

    embedded = "Here is the result: {\"status\": \"ok\"} Thanks!"
    assert client.extract_json(embedded) == "{\"status\": \"ok\"}"


def test_mock_engine_triage_structured():
    client = GemmaClient(backend="mock")
    prompt = "Triage target dependency: toml"
    result = client.generate_structured(prompt, ReplacementRecommendation)
    assert result.target_dependency == "toml"
    assert result.recommended_choice == "tomllib"
    assert len(result.options) >= 2
