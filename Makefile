.PHONY: help install test lint typecheck format check build clean

help:
	@echo "Available commands:"
	@echo "  install      Install dependencies with uv"
	@echo "  test         Run tests with coverage"
	@echo "  lint         Run ruff linter"
	@echo "  typecheck    Run mypy type checker"
	@echo "  format       Format code with ruff"
	@echo "  check        Run all checks (lint, typecheck, test)"
	@echo "  build        Build package with uv"
	@echo "  clean        Clean build artifacts"

install:
	uv sync --all-extras

test:
	uv run pytest --cov=src/db_agent --cov-report=term-missing

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

format:
	uv run ruff format .
	uv run ruff check --fix .

check: lint typecheck test

build:
	uv build

clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache __pycache__ src/__pycache__ src/db_agent/__pycache__ tests/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete