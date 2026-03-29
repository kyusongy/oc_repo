import pytest
from backend.agent.llm import get_client


def test_get_client_reads_env(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://test.api.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    client = get_client()
    assert client.base_url.host == "test.api.com"


def test_get_client_missing_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        get_client()
