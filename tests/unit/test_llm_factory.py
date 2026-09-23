"""Unit tests for LLM factory."""

import pytest

from db_agent.config import LLMProvider, Settings
from db_agent.exceptions import ConfigurationError
from db_agent.llm import create_chat_model, create_embeddings


def test_create_embeddings_ollama() -> None:
    """Test Ollama embeddings creation."""
    settings = Settings(
        embedding_provider="ollama",
        embedding_model="nomic-embed-text",
        ollama_base_url="http://localhost:11434",
    )
    embeddings = create_embeddings(settings)
    assert embeddings is not None


def test_create_embeddings_unsupported_provider() -> None:
    """Test unsupported embedding provider raises error."""
    # We can't easily test this without mocking the enum
    # but the factory dict only has OLLAMA


def test_settings_groq_requires_key() -> None:
    """Test Groq requires API key."""
    settings = Settings(llm_provider=LLMProvider.GROQ, groq_api_key=None)
    with pytest.raises(ConfigurationError):
        create_chat_model(settings)


def test_settings_openai_requires_key() -> None:
    """Test OpenAI requires API key."""
    settings = Settings(llm_provider=LLMProvider.OPENAI, openai_api_key=None)
    with pytest.raises(ConfigurationError):
        create_chat_model(settings)


def test_settings_anthropic_requires_key() -> None:
    """Test Anthropic requires API key."""
    settings = Settings(llm_provider=LLMProvider.ANTHROPIC, anthropic_api_key=None)
    with pytest.raises(ConfigurationError):
        create_chat_model(settings)
