"""Constants for db-design-agent."""

from pathlib import Path

# Configuration defaults
DEFAULT_MAX_CONTEXT_PREVIEW = 100
DEFAULT_MAX_QUERY_LENGTH = 1000
DEFAULT_PATTERN_TRUNCATE_LENGTH = 500
DEFAULT_RATE_LIMIT_MAX = 5
DEFAULT_RATE_LIMIT_WINDOW = 60.0
DEFAULT_OLLAMA_MODELS_DISPLAY = 5
DEFAULT_EMBEDDING_LENGTH = 768
DEFAULT_CONTROL_CHAR_THRESHOLD = 32
DEFAULT_PREVIEW_LENGTH = 200

# Allowed DDL statements
ALLOWED_DDL_STATEMENTS = frozenset({
    "CREATE TABLE",
    "CREATE INDEX",
    "CREATE UNIQUE INDEX",
    "COMMENT ON",
    "ALTER TABLE",
})

# Default models per provider
DEFAULT_MODELS = {
    "groq": "llama-3.1-70b-versatile",
    "ollama": "llama3.1:8b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-haiku-20240307",
}

# Default embedding models per provider
DEFAULT_EMBEDDING_MODELS = {
    "ollama": "nomic-embed-text",
    "openai": "text-embedding-3-small",
    "cohere": "embed-english-v3.0",
}

# Output formats
VALID_OUTPUT_FORMATS = frozenset({"json", "sql", "md"})

# Default output directory
DEFAULT_OUTPUT_DIR = Path("./output")
DEFAULT_CHROMA_DIR = Path("./chroma_db")
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_LOG_LEVEL = "INFO"

# Max clarification rounds in interactive mode
MAX_ROUNDS = 3
