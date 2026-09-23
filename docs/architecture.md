# Architecture

## Overview

db-design-agent uses a **LangGraph** workflow with four sequential nodes:

```
Business Context → Retrieve → Design → Dictionary → DDL → Output
```

Each node is a pure function with injected dependencies, making the graph testable and composable.

## Components

### 1. Configuration (`config.py`)

- `Settings` class using `pydantic-settings`
- Loads from environment variables with `DB_AGENT_` prefix
- Supports `.env` files in `~/.config/db-design-agent/` and cwd
- Frozen (immutable) after initialization
- Secrets wrapped in `SecretStr`

### 2. LLM Factory (`llm.py`)

- **Strategy Pattern**: Provider-specific factories implement `ChatModelFactory` protocol
- **Registry**: `_CHAT_FACTORIES` maps `LLMProvider` enum to factory instances
- **Error handling**: Wraps provider errors in `LLMProviderError` / `ConfigurationError`
- **Lazy imports**: Provider packages only imported when needed

### 3. Knowledge Base (`knowledge/loader.py`)

- Embedded patterns content (`_PATTERNS_CONTENT`)
- `RecursiveCharacterTextSplitter` for chunking (500 chars, 50 overlap)
- ChromaDB vectorstore with Ollama embeddings (`nomic-embed-text`)
- Idempotent loading: only populates if collection is empty
- Similarity search with configurable `k`

### 4. Nodes (`nodes/`)

Each node is a pure function:
- `retrieve_node`: Vector similarity search → patterns
- `design_node`: LLM + JSON parser → `DatabaseSchema`
- `dictionary_node`: LLM + JSON parser → `list[DataDictionaryEntry]`
- `ddl_node`: LLM → raw SQL string

Dependencies injected via `functools.partial` in `graph.py`.

### 5. Graph (`graph.py`)

- `StateGraph(AgentState)` with four nodes
- `build_graph(settings, cwd)` compiles workflow with DI
- `run_agent(context, settings, cwd)` async entry point
- Uses `ainvoke` for async execution

### 6. Models (`models.py`)

Pydantic models with:
- `frozen=True, slots=True` for immutability/performance
- `extra="forbid"` for strict validation
- Field constraints (min_length, patterns)
- `AgentState` as graph state container

### 7. CLI (`cli.py`)

- Typer app with rich output
- Commands: `design`, `config`, `doctor`, `version`
- Interactive wizard for first-time setup
- Health checks for Ollama, ChromaDB, dependencies

## Data Flow

```
User Input (context string)
        │
        ▼
┌───────────────────────┐
│   Settings + DI       │
│  - LLM (provider)     │
│  - Embeddings         │
│  - Vectorstore        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Retrieve Node       │
│  context → embedding  │
│  → similarity search  │
│  → patterns[]         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Design Node         │
│  context + patterns   │
│  → LLM (structured)   │
│  → DatabaseSchema     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Dictionary Node     │
│  schema → LLM         │
│  → DataDictionary[]   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   DDL Node            │
│  schema → LLM         │
│  → SQL string         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Output              │
│  - schema.json        │
│  - dictionary.md/json │
│  - schema.sql         │
└───────────────────────┘
```

## Security Considerations

- **Secrets**: Never logged, only in memory via `SecretStr`
- **Input validation**: All user input validated by Pydantic
- **Path safety**: Output directories resolved absolutely, checked against cwd
- **SSRF protection**: `HttpUrl` validation for Ollama base URL
- **No dynamic code**: No `eval`, `exec`, or template injection

## Extensibility

### Adding LLM Provider

1. Add to `LLMProvider` enum
2. Implement `ChatModelFactory` protocol
3. Register in `_CHAT_FACTORIES`
4. Add optional dependency in `pyproject.toml`

### Adding Embedding Provider

1. Add to `EmbeddingProvider` enum
2. Implement `EmbeddingsFactory` protocol
3. Register in `_EMBEDDINGS_FACTORIES`
4. Update `knowledge/loader.py` to use new provider

### Adding Output Format

1. Add formatter function in `output.py`
2. Update `save_outputs` and `OutputFormat` type
3. Add CLI option in `cli.py`