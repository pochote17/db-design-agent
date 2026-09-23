# db-design-agent

AI agent for database schema design from business context. Describe your business domain in natural language and get a complete PostgreSQL schema with data dictionary and DDL.

## Features

- **Natural language input**: Describe your business context in plain text
- **Multiple LLM providers**: Groq, Ollama (local), OpenAI, Anthropic
- **RAG-enhanced**: Retrieves relevant database design patterns for better results
- **Complete output**: Schema (JSON), Data Dictionary (Markdown/JSON), SQL DDL (PostgreSQL)
- **CLI & Library**: Use as command-line tool or import in Python
- **Zero-config local**: Works with Ollama for fully offline usage
- **Security-first**: Prompt injection detection, SQL injection prevention, rate limiting, audit logging

## Quick Start

### Installation

```bash
# Using pipx (recommended for CLI tools)
pipx install db-design-agent

# Using uv (fast)
uvx db-design-agent

# Using pip
pip install db-design-agent
```

### Configuration

Run the interactive wizard:

```bash
db-design-agent config --wizard
```

Or set environment variables:

```bash
export DB_AGENT_LLM_PROVIDER=groq
export DB_AGENT_GROQ_API_KEY=your_key_here
export DB_AGENT_LLM_MODEL=llama-3.1-70b-versatile
```

### Usage

```bash
# Basic usage (uses Ollama locally by default)
db-design-agent design "E-commerce platform with users, products, orders, and payments"

# With specific provider
db-design-agent design "SaaS with tenants, subscriptions, and billing" --provider ollama --model llama3.1:8b

# Custom output formats
db-design-agent design "..." --format json,sql

# Verbose output
db-design-agent design "..." --verbose
```

### Output Files

The agent generates three files in `./output/` by default:

| File | Description |
|------|-------------|
| `schema.json` | Complete database schema with tables, columns, indexes, relationships |
| `dictionary.md` | Human-readable data dictionary with business meanings |
| `schema.sql` | Production-ready PostgreSQL DDL |

## Requirements

- **Python 3.10+**
- **LLM Provider** (one of):
  - Groq API key (free tier available at console.groq.com)
  - Ollama running locally (`ollama serve`)
  - OpenAI API key
  - Anthropic API key
- For embeddings: **Ollama** with `nomic-embed-text` model (`ollama pull nomic-embed-text`)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Business   │────▶│  Retrieval  │────▶│   Design    │
│  Context    │     │  (RAG)      │     │   Schema    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Output    │◀────│  Data Dict  │◀────│   DDL Gen   │
│  (JSON/SQL/ │     │  Generation │     │             │
│   Markdown) │     └─────────────┘     └─────────────┘
```

1. **Retrieval**: Embeds business context, retrieves relevant patterns from knowledge base
2. **Design**: LLM generates normalized schema (tables, columns, relationships, indexes)
3. **Dictionary**: LLM creates technical-business data dictionary
4. **DDL**: LLM produces PostgreSQL DDL with constraints, indexes, comments

## Configuration

Configuration is loaded from (in order of precedence):
1. Environment variables (`DB_AGENT_*`)
2. `~/.config/db-design-agent/.env`
3. `.env` in current working directory
4. Defaults

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_AGENT_LLM_PROVIDER` | LLM provider (groq, ollama, openai, anthropic) | ollama |
| `DB_AGENT_LLM_MODEL` | Model name | provider-specific default |
| `DB_AGENT_GROQ_API_KEY` | Groq API key | - |
| `DB_AGENT_OPENAI_API_KEY` | OpenAI API key | - |
| `DB_AGENT_ANTHROPIC_API_KEY` | Anthropic API key | - |
| `DB_AGENT_OLLAMA_BASE_URL` | Ollama base URL | http://localhost:11434 |
| `DB_AGENT_EMBEDDING_MODEL` | Embedding model | nomic-embed-text |
| `DB_AGENT_CHROMA_PERSIST_DIR` | ChromaDB directory | ./chroma_db |
| `DB_AGENT_OUTPUT_DIR` | Output directory | ./output |
| `DB_AGENT_LOG_LEVEL` | Log level | INFO |

### Default Models per Provider

| Provider | Default Model |
|----------|---------------|
| Groq | `llama-3.1-70b-versatile` |
| Ollama | `llama3.1:8b` |
| OpenAI | `gpt-4o-mini` |
| Anthropic | `claude-3-haiku-20240307` |

## Security

db-design-agent implements multiple layers of security:

- **Prompt Injection Detection**: Regex-based detection of common injection patterns (ignore instructions, roleplay, system prompt extraction). Detected attempts are blocked and logged.
- **SQL Injection Prevention**: Generated DDL is validated against a forbidden pattern list (DML, dangerous DDL, transaction control) and parsed with `sqlparse` to ensure only allowed statements (`CREATE TABLE`, `CREATE INDEX`, `COMMENT ON`, `ALTER TABLE` with constraints).
- **Input Validation**: All user inputs validated (max 10,000 chars context, 1,000 chars query). Control characters removed, length limited, curly braces escaped.
- **Rate Limiting**: CLI `design` command limited to 5 requests/minute per process.
- **Audit Logging**: Security events (prompt injection, SQL injection, validation failures) logged to `./logs/security.log`.
- **Path Safety**: Output directories resolved absolutely, symlinks resolved, traversal prevented.
- **Secrets**: `SecretStr` for API keys, never logged, excluded from serialization.

See [docs/security.md](docs/security.md) for full details.

## Development

### Setup

```bash
git clone https://github.com/user/db-design-agent
cd db-design-agent

# Install with dev dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Commands

```bash
# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck

# Run all checks
make check

# Format code
make format

# Build package
make build
```

### Project Structure

```
src/db_agent/
├── cli.py              # Typer CLI application
├── config.py           # Settings management (pydantic-settings)
├── models.py           # Pydantic models (frozen, slots)
├── prompts.py          # Prompt templates
├── llm.py              # LLM factory (provider abstraction)
├── graph.py            # LangGraph workflow compilation
├── security.py         # Security utilities (sanitization, validation, logging)
├── knowledge/
│   └── loader.py       # Knowledge base (embedded patterns)
├── nodes/
│   ├── retrieve.py     # Pattern retrieval
│   ├── design.py       # Schema design
│   ├── dictionary.py   # Data dictionary generation
│   └── ddl.py          # DDL generation
├── output.py           # Output formatting & file saving
└── exceptions.py       # Custom exceptions
```

## Docker

### With Groq (default)

```bash
docker run --rm \
  -e DB_AGENT_GROQ_API_KEY=your_key \
  -v $(pwd)/output:/app/output \
  ghcr.io/user/db-design-agent:latest \
  design "Your business context"
```

### With Local Ollama

```bash
# Start Ollama
docker compose -f docker/docker-compose.yml --profile local up -d ollama

# Pull model
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull nomic-embed-text

# Run agent
docker compose -f docker/docker-compose.yml --profile local run --rm \
  -e DB_AGENT_LLM_PROVIDER=ollama \
  db-design-agent design "Your business context"
```

## Security

db-design-agent implements multiple layers of security:

- **Prompt Injection Detection**: Regex-based detection of common injection patterns (ignore instructions, roleplay, system prompt extraction). Detected attempts are blocked and logged.
- **SQL Injection Prevention**: Generated DDL is validated against a forbidden pattern list (DML, dangerous DDL, transaction control) and parsed with `sqlparse` to ensure only allowed statements (`CREATE TABLE`, `CREATE INDEX`, `COMMENT ON`, `ALTER TABLE` with constraints).
- **Input Validation**: All user inputs validated (max 10,000 chars context, 1,000 chars query). Control characters removed, length limited, curly braces escaped.
- **Rate Limiting**: CLI `design` command limited to 5 requests/minute per process.
- **Audit Logging**: Security events (prompt injection, SQL injection, validation failures) logged to `./logs/security.log`.
- **Path Safety**: Output directories resolved absolutely, symlinks resolved, traversal prevented.
- **Secrets**: `SecretStr` for API keys, never logged, excluded from serialization.

See [docs/security.md](docs/security.md) for full details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.