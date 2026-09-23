# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src ./src

# Install project
RUN uv sync --frozen --no-dev


# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy from builder
COPY --from=builder /app /app

# Create directories
RUN mkdir -p /app/data /app/output && chown -R appuser:appuser /app

USER appuser

# Environment
ENV PYTHONUNBUFFERED=1
ENV DB_AGENT_CHROMA_PERSIST_DIR=/app/data/chroma
ENV DB_AGENT_OUTPUT_DIR=/app/output

ENTRYPOINT ["db-design-agent"]
CMD ["--help"]