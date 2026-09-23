"""Unit tests for configuration."""

from pathlib import Path

import pytest

from db_agent.config import EmbeddingProvider, LLMProvider, Settings


def test_default_settings() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.llm_provider == LLMProvider.OLLAMA
    assert settings.llm_model == "llama3.1:8b"
    assert settings.embedding_provider == EmbeddingProvider.OLLAMA
    assert settings.embedding_model == "nomic-embed-text"


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test settings loaded from environment variables."""
    monkeypatch.setenv("DB_AGENT_LLM_PROVIDER", "groq")
    monkeypatch.setenv("DB_AGENT_LLM_MODEL", "llama-3.1-70b-versatile")
    monkeypatch.setenv("DB_AGENT_GROQ_API_KEY", "test-key")
    monkeypatch.setenv("DB_AGENT_LOG_LEVEL", "DEBUG")

    settings = Settings()
    assert settings.llm_provider == LLMProvider.GROQ
    assert settings.llm_model == "llama-3.1-70b-versatile"
    assert settings.groq_api_key is not None
    assert settings.groq_api_key.get_secret_value() == "test-key"
    assert settings.log_level == "DEBUG"


def test_settings_immutable() -> None:
    """Test settings are frozen/immutable."""
    settings = Settings()
    with pytest.raises(Exception):
        settings.llm_provider = LLMProvider.OLLAMA


def test_resolve_output_dir() -> None:
    """Test output directory resolution."""
    settings = Settings(output_dir=Path("custom_output"))
    resolved = settings.resolve_output_dir(Path("/tmp"))
    assert resolved == Path("/tmp/custom_output").resolve()


def test_resolve_chroma_dir() -> None:
    """Test ChromaDB directory resolution."""
    settings = Settings(chroma_persist_dir=Path("custom_chroma"))
    resolved = settings.resolve_chroma_dir(Path("/tmp"))
    assert resolved == Path("/tmp/custom_chroma").resolve()


def test_get_default_model() -> None:
    """Test default model per provider."""
    settings = Settings()
    assert settings.get_default_model(LLMProvider.GROQ) == "llama-3.1-70b-versatile"
    assert settings.get_default_model(LLMProvider.OLLAMA) == "llama3.1:8b"
    assert settings.get_default_model(LLMProvider.OPENAI) == "gpt-4o-mini"
    assert settings.get_default_model(LLMProvider.ANTHROPIC) == "claude-3-haiku-20240307"
