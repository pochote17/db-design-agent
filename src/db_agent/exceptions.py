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


class ValidationErrorCode:
    """Error codes for validation errors."""
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"
    EMPTY_DDL_OUTPUT = "EMPTY_DDL_OUTPUT"
    FORBIDDEN_SQL_PATTERN = "FORBIDDEN_SQL_PATTERN"
    SQL_PARSE_FAILED = "SQL_PARSE_FAILED"
    DISALLOWED_SQL_STATEMENT = "DISALLOWED_SQL_STATEMENT"
    DISALLOWED_ALTER_TABLE = "DISALLOWED_ALTER_TABLE"
    EMPTY_CONTEXT = "EMPTY_CONTEXT"


class ValidationError(AgentError):
    """Raised when output validation fails."""

    def __init__(self, code: str, field: str | None = None):
        messages = {
            "PROMPT_INJECTION_DETECTED": "Potential prompt injection detected",
            "INPUT_TOO_LONG": "Input exceeds maximum length",
            "EMPTY_DDL_OUTPUT": "Empty DDL output",
            "FORBIDDEN_SQL_PATTERN": "Forbidden SQL pattern detected",
            "SQL_PARSE_FAILED": "Failed to parse SQL",
            "DISALLOWED_SQL_STATEMENT": "Disallowed SQL statement type",
            "DISALLOWED_ALTER_TABLE": "Disallowed ALTER TABLE operation",
            "EMPTY_CONTEXT": "Business context cannot be empty",
        }
        message = messages.get(code, "Validation error")
        super().__init__(message, code)
        self.field = field


class OutputError(AgentError):
    """Raised when output generation or file writing fails."""

    def __init__(self, message: str, path: str | None = None):
        super().__init__(message, "OUTPUT_ERROR")
        self.path = path


class ValidationErrorCodes:
    """Error codes for validation errors (backward compatibility)."""
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"
    EMPTY_DDL_OUTPUT = "EMPTY_DDL_OUTPUT"
    FORBIDDEN_SQL_PATTERN = "FORBIDDEN_SQL_PATTERN"
    SQL_PARSE_FAILED = "SQL_PARSE_FAILED"
    DISALLOWED_SQL_STATEMENT = "DISALLOWED_SQL_STATEMENT"
    DISALLOWED_ALTER_TABLE = "DISALLOWED_ALTER_TABLE"
    EMPTY_CONTEXT = "EMPTY_CONTEXT"