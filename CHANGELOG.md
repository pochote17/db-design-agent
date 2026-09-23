# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-09-23

### Added
- Initial project structure with modular architecture
- Multi-provider LLM support (Groq, Ollama, OpenAI, Anthropic) via factory pattern
- RAG-enhanced schema design with embedded database design patterns
- LangGraph workflow: retrieve → design → dictionary → DDL
- CLI with design, config, doctor, version commands (Typer + Rich)
- Output formats: JSON schema, Markdown dictionary, SQL DDL (PostgreSQL)
- Pydantic models with frozen/slots for performance and immutability
- Embedded knowledge base with database design patterns (normalization, star/snowflake schemas, SCD, domain patterns)
- ChromaDB vectorstore with Ollama embeddings (nomic-embed-text)
- Config file discovery: cwd `.env` → `~/.config/db-design-agent/.env` → `~/.env`
- Interactive configuration wizard writing to both project `.env` and user config dir
- Docker multi-stage build with Ollama profile for local development
- GitHub Actions CI (ruff, mypy, pytest with coverage) and Release workflows (PyPI + GHCR)

### Security
- **Prompt Injection Detection**: Regex-based detection of common injection patterns (ignore instructions, roleplay, system prompt extraction). Blocked attempts raise `ValidationError` and are logged.
- **SQL Injection Prevention**: Generated DDL validated against forbidden patterns (DML, dangerous DDL, transaction control) and parsed with `sqlparse` to ensure only allowed statements (`CREATE TABLE`, `CREATE INDEX`, `COMMENT ON`, `ALTER TABLE` with `ADD CONSTRAINT/COLUMN`).
- **Input Validation**: All user inputs validated (max 10,000 chars context, 1,000 chars query). Control characters removed, length limited, curly braces escaped for template safety.
- **Rate Limiting**: CLI `design` command limited to 5 requests/minute per process (in-memory deque).
- **Audit Logging**: Security events (prompt injection, SQL injection, validation failures) logged to `./logs/security.log` with timestamp, event type, detail, and truncated input sample.
- **Path Safety**: Output directories resolved absolutely, symlinks resolved, traversal prevented.
- **Secrets Handling**: `SecretStr` for API keys, never logged, excluded from serialization, only passed to provider SDK at call time.
- **SSRF Protection**: `HttpUrl` validation for Ollama base URL, `follow_redirects=True` with final status check.

### Changed
- Default LLM provider changed from Groq to Ollama for zero-config local usage
- Default Ollama model changed from `gemma4:12b` to standard `llama3.1:8b`
- Config file discovery priority: cwd `.env` → `~/.config/db-design-agent/.env` → `~/.env`
- Wizard now writes to project `.env` (priority) and user config directory
- `config_file` parameter now functional via `_env_file` override
- Ollama health check uses `response.is_success` and `follow_redirects=True` to handle 301/307 redirects

### Fixed
- Design command now validates `settings.llm_provider` instead of CLI option
- Ollama health check now handles HTTP 301/307 redirects correctly
- Rate limiting (5 requests/minute) added to `design` command

### Dependencies
- Added `sqlparse>=0.5` for SQL parsing and validation
- Minimum Python version: 3.10

## [0.0.1] - 2024-XX-XX

### Added
- Initial project structure
- Multi-provider LLM support (Groq, Ollama, OpenAI, Anthropic)
- RAG-enhanced schema design with embedded patterns
- CLI with design, config, doctor, version commands
- Output formats: JSON, SQL, Markdown
- Docker support with Ollama profile
- Comprehensive test suite (unit + integration)
- CI/CD with GitHub Actions
- Security-focused configuration with SecretStr