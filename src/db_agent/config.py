"""Configuration management for db-design-agent."""

from enum import StrEnum
from pathlib import Path

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    """Supported LLM providers."""

    GROQ = "groq"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class EmbeddingProvider(StrEnum):
    """Supported embedding providers."""

    OLLAMA = "ollama"


class Settings(BaseSettings):
    """Application settings loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DB_AGENT_",
        extra="ignore",
        frozen=True,
    )

    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.GROQ
    llm_model: str = "llama-3.1-70b-versatile"
    groq_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    ollama_base_url: HttpUrl = "http://localhost:11434"

    # Embeddings (Ollama only for v0.1)
    embedding_provider: EmbeddingProvider = EmbeddingProvider.OLLAMA
    embedding_model: str = "nomic-embed-text"

    # Vector Database
    chroma_persist_dir: Path = Path("./chroma_db")

    # Application
    log_level: str = "INFO"
    output_dir: Path = Path("./output")

    # Default models per provider
    @property
    def default_models(self) -> dict[LLMProvider, str]:
        return {
            LLMProvider.GROQ: "llama-3.1-70b-versatile",
            LLMProvider.OLLAMA: "llama3.1:8b",
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.ANTHROPIC: "claude-3-haiku-20240307",
        }

    def get_default_model(self, provider: LLMProvider) -> str:
        """Get default model for a provider."""
        return self.default_models.get(provider, "llama-3.1-70b-versatile")

    def resolve_output_dir(self, cwd: Path) -> Path:
        """Resolve output directory relative to working directory."""
        output_dir = self.output_dir
        if not output_dir.is_absolute():
            output_dir = cwd / output_dir
        return output_dir.resolve()

    def resolve_chroma_dir(self, cwd: Path) -> Path:
        """Resolve ChromaDB directory relative to working directory."""
        chroma_dir = self.chroma_persist_dir
        if not chroma_dir.is_absolute():
            chroma_dir = cwd / chroma_dir
        return chroma_dir.resolve()


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
