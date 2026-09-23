# Contributing to db-design-agent

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/db-design-agent`
3. Install dependencies: `uv sync --all-extras`
4. Install pre-commit hooks: `uv run pre-commit install`
5. Create a branch: `git checkout -b feature/your-feature`

## Development Workflow

### Code Style

- **Formatter**: Ruff (configured in `pyproject.toml`)
- **Linter**: Ruff
- **Type checker**: mypy (strict mode)
- **Tests**: pytest with coverage

Run all checks:

```bash
make check
```

Individual commands:

```bash
make format      # Format code with ruff
make lint        # Lint with ruff
make typecheck   # Type check with mypy
make test        # Run tests with pytest
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new LLM provider support
fix: handle empty context in design node
docs: update README with Docker examples
test: add integration test for graph compilation
refactor: extract prompt templates to separate module
```

### Pull Requests

1. Ensure all checks pass (`make check`)
2. Update tests for new functionality
3. Update documentation if needed
4. Keep PRs focused and atomic
5. Reference related issues

## Testing

### Unit Tests

```bash
uv run pytest tests/unit -v
```

### Integration Tests

```bash
uv run pytest tests/integration -v
```

### Coverage

```bash
uv run pytest --cov=src/db_agent --cov-report=html
```

## Adding a New LLM Provider

1. Add provider to `LLMProvider` enum in `config.py`
2. Create factory class in `llm.py` following existing pattern
3. Register in `_CHAT_FACTORIES` dict
4. Add optional dependency in `pyproject.toml`
5. Add tests in `tests/unit/test_llm_factory.py`
6. Update documentation

## Code Guidelines

- **Type hints**: All functions must have type hints
- **Docstrings**: Public functions/classes need docstrings
- **Error handling**: Use custom exceptions from `exceptions.py`
- **Immutability**: Use `frozen=True, slots=True` for Pydantic models
- **No emojis** in source code (CLI output OK)
- **Security**: Never log secrets, validate all inputs

## Reporting Issues

- Use issue templates
- Provide minimal reproduction case
- Include environment details (OS, Python version, provider)
- Check existing issues first

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).