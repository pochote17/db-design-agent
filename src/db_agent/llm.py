"""LLM factory for creating chat models and embeddings."""

from typing import Protocol

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

try:
    from langchain_groq import ChatGroq
except ImportError:  # pragma: no cover
    ChatGroq = None  # type: ignore

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover
    ChatOllama = None  # type: ignore

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:  # pragma: no cover
    ChatAnthropic = None  # type: ignore

try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:  # pragma: no cover
    OllamaEmbeddings = None  # type: ignore

try:
    from langchain_cohere import CohereEmbeddings
except ImportError:  # pragma: no cover
    CohereEmbeddings = None  # type: ignore

from .config import EmbeddingProvider, LLMProvider, Settings
from .exceptions import ConfigurationError, LLMProviderError


class ChatModelFactory(Protocol):
    """Protocol for chat model factories."""

    def create_chat(self, settings: Settings) -> BaseChatModel: ...


class EmbeddingsFactory(Protocol):
    """Protocol for embeddings factories."""

    def create_embeddings(self, settings: Settings) -> Embeddings: ...


class GroqChatFactory:
    """Factory for Groq chat models."""

    def create_chat(self, settings: Settings) -> BaseChatModel:
        if ChatGroq is None:
            raise ConfigurationError(
                "langchain-groq not installed. Install with: pip install db-design-agent[groq]"
            )

        if not settings.groq_api_key:
            raise ConfigurationError("GROQ_API_KEY is required for Groq provider")

        return ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key.get_secret_value(),
            temperature=0.1,
        )


class OllamaChatFactory:
    """Factory for Ollama chat models."""

    def create_chat(self, settings: Settings) -> BaseChatModel:
        if ChatOllama is None:
            raise ConfigurationError(
                "langchain-ollama not installed. Install with: pip install db-design-agent[ollama]"
            )

        return ChatOllama(
            model=settings.llm_model,
            base_url=str(settings.ollama_base_url),
            temperature=0.1,
        )


class OpenAIChatFactory:
    """Factory for OpenAI chat models."""

    def create_chat(self, settings: Settings) -> BaseChatModel:
        if ChatOpenAI is None:
            raise ConfigurationError(
                "langchain-openai not installed. Install with: pip install db-design-agent[openai]"
            )

        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for OpenAI provider")

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key.get_secret_value(),
            temperature=0.1,
        )


class AnthropicChatFactory:
    """Factory for Anthropic chat models."""

    def create_chat(self, settings: Settings) -> BaseChatModel:
        if ChatAnthropic is None:
            raise ConfigurationError(
                "langchain-anthropic not installed. Install with: pip install db-design-agent[anthropic]"
            )

        if not settings.anthropic_api_key:
            raise ConfigurationError("ANTHROPIC_API_KEY is required for Anthropic provider")

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key.get_secret_value(),
            temperature=0.1,
        )


class OllamaEmbeddingsFactory:
    """Factory for Ollama embeddings."""

    def create_embeddings(self, settings: Settings) -> Embeddings:
        if OllamaEmbeddings is None:
            raise ConfigurationError(
                "langchain-ollama not installed. Install with: pip install db-design-agent[ollama]"
            )

        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=str(settings.ollama_base_url),
        )


class OpenAIEmbeddingsFactory:
    """Factory for OpenAI embeddings."""

    def create_embeddings(self, settings: Settings) -> Embeddings:
        if OpenAIEmbeddings is None:
            raise ConfigurationError(
                "langchain-openai not installed. Install with: pip install db-design-agent[openai]"
            )

        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for OpenAI embeddings")

        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key.get_secret_value(),
        )


class CohereEmbeddingsFactory:
    """Factory for Cohere embeddings."""

    def create_embeddings(self, settings: Settings) -> Embeddings:
        if CohereEmbeddings is None:
            raise ConfigurationError(
                "langchain-cohere not installed. Install with: pip install db-design-agent[cohere]"
            )

        if not settings.cohere_api_key:
            raise ConfigurationError("COHERE_API_KEY is required for Cohere embeddings")

        return CohereEmbeddings(
            model=settings.embedding_model,
            cohere_api_key=settings.cohere_api_key.get_secret_value(),
        )


_CHAT_FACTORIES: dict[LLMProvider, ChatModelFactory] = {
    LLMProvider.GROQ: GroqChatFactory(),
    LLMProvider.OLLAMA: OllamaChatFactory(),
    LLMProvider.OPENAI: OpenAIChatFactory(),
    LLMProvider.ANTHROPIC: AnthropicChatFactory(),
}

_EMBEDDINGS_FACTORIES: dict[EmbeddingProvider, EmbeddingsFactory] = {
    EmbeddingProvider.OLLAMA: OllamaEmbeddingsFactory(),
    EmbeddingProvider.OPENAI: OpenAIEmbeddingsFactory(),
    EmbeddingProvider.COHERE: CohereEmbeddingsFactory(),
}


def create_chat_model(settings: Settings) -> BaseChatModel:
    """Create chat model based on settings."""
    factory = _CHAT_FACTORIES.get(settings.llm_provider)
    if not factory:
        raise LLMProviderError(
            f"Unsupported LLM provider: {settings.llm_provider}",
            settings.llm_provider.value,
        )
    try:
        return factory.create_chat(settings)
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise LLMProviderError(
            f"Failed to create chat model for {settings.llm_provider}: {e}",
            settings.llm_provider.value,
        ) from e


def create_embeddings(settings: Settings) -> Embeddings:
    """Create embeddings model based on settings."""
    factory = _EMBEDDINGS_FACTORIES.get(settings.embedding_provider)
    if not factory:
        raise LLMProviderError(
            f"Unsupported embedding provider: {settings.embedding_provider}",
            settings.embedding_provider.value,
        )
    try:
        return factory.create_embeddings(settings)
    except Exception as e:
        raise LLMProviderError(
            f"Failed to create embeddings for {settings.embedding_provider}: {e}",
            settings.embedding_provider.value,
        ) from e
