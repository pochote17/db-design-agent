# Configuration

## Overview

db-design-agent uses a layered configuration approach with the following precedence (highest to lowest):

1. Environment variables (`DB_AGENT_*`)
2. `~/.config/db-design-agent/.env`
3. `.env` in current working directory
3. Default values

## Environment Variables

### LLM Provider

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_AGENT_LLM_PROVIDER` | Provider: `groq`, `ollama`, `openai`, `anthropic` | `groq` |
| `DB_AGENT_LLM_MODEL` | Model name | Provider-specific default |

### API Keys

| Variable | Provider | Required |
|----------|----------|----------|
| `DB_AGENT_GROQ_API_KEY` | Groq | Yes (if provider=groq) |
| `DB_AGENT_OPENAI_API_KEY` | OpenAI | Yes (if provider=openai) |
| `DB_AGENT_ANTHROPIC_API_KEY` | Anthropic | Yes (if provider=anthropic) |

### Ollama

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_AGENT_OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |

### Embeddings

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_AGENT_EMBEDDING_MODEL` | Embedding model name | `nomic-embed-text` |

### Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_AGENT_CHROMA_PERSIST_DIR` | ChromaDB persistence directory | `./chroma_db` |
| `DB_AGENT_OUTPUT_DIR` | Output files directory | `./output` |

### Logging

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_AGENT_LOG_LEVEL` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

## Default Models

| Provider | Default Model |
|----------|---------------|
| Groq | `llama-3.1-70b-versatile` |
| Ollama | `llama3.1:8b` |
| OpenAI | `gpt-4o-mini` |
| Anthropic | `claude-3-haiku-20240307` |

## Configuration File

The wizard creates `~/.config/db-design-agent/.env`:

```bash
DB_AGENT_LLM_PROVIDER=groq
DB_AGENT_LLM_MODEL=llama-3.1-70b-versatile
DB_AGENT_GROQ_API_KEY=your_key_here
```

## Provider Setup

### Groq (Recommended for Cloud)

1. Create account at https://console.groq.com
2. Generate API key
3. Set `DB_AGENT_GROQ_API_KEY` or run wizard

### Ollama (Local)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start server
ollama serve

# Pull models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Configure
export DB_AGENT_LLM_PROVIDER=ollama
export DB_AGENT_LLM_MODEL=llama3.1:8b
```

### OpenAI

```bash
export DB_AGENT_LLM_PROVIDER=openai
export DB_AGENT_OPENAI_API_KEY=sk-...
export DB_AGENT_LLM_MODEL=gpt-4o-mini
```

### Anthropic

```bash
export DB_AGENT_LLM_PROVIDER=anthropic
export DB_AGENT_ANTHROPIC_API_KEY=sk-ant-...
export DB_AGENT_LLM_MODEL=claude-3-haiku-20240307
```

## Verification

Run health check:

```bash
db-design-agent doctor
```

Output shows status of:
- Configuration validity
- Ollama connectivity (if used)
- ChromaDB directory
- Output directory
- All Python dependencies