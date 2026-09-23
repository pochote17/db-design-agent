"""Custom exceptions for db-design-agent."""


class AgentError(Exception):
    """Base exception for agent errors."""

    def __init__(self, message: str, code: str = "AGENT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigurationError(AgentError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")


class LLMProviderError(AgentError):
    """Raised when LLM provider fails or is unavailable."""

    def __init__(self, message: str, provider: str):
        super().__init__(message, "LLM_PROVIDER_ERROR")
        self.provider = provider


class KnowledgeBaseError(AgentError):
    """Raised when knowledge base operations fail."""

    def __init__(self, message: str):
        super().__init__(message, "KNOWLEDGE_BASE_ERROR")


class ValidationError(AgentError):
    """Raised when output validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field


class OutputError(AgentError):
    """Raised when output generation or file writing fails."""

    def __init__(self, message: str, path: str | None = None):
        super().__init__(message, "OUTPUT_ERROR")
        self.path = path
