# Security

## Threat Model

db-design-agent is a CLI tool that:
- Accepts user-provided business context (text input)
- Calls external LLM APIs or local Ollama
- Stores embeddings in local ChromaDB
- Writes output files to local filesystem

### Attack Vectors

1. **Prompt Injection**: Malicious context attempting to alter agent behavior
2. **SQL Injection**: Malicious LLM output attempting to execute arbitrary SQL
3. **Path Traversal**: Output directory manipulation to write outside intended location
4. **Secret Exposure**: API keys leaked in logs, errors, or output files
5. **SSRF**: Ollama base URL pointing to internal services
6. **Dependency Confusion**: Malicious packages in supply chain

## Mitigations

### Input Validation

- Business context: Plain text, max 10,000 chars, no markup interpretation
- Query for vector search: Max 1,000 chars
- Pydantic models validate all structured data with `extra="forbid"`
- Input sanitization: control chars removed, length limited, whitespace normalized

### Prompt Injection Protection

- **Detection**: Regex patterns for common injection attempts (ignore instructions, roleplay, system prompt extraction, etc.)
- **Validation**: All user inputs validated before being passed to LLM
- **Sanitization**: Curly braces escaped (`{` → `{{`, `}` → `}}`) to prevent template injection
- **Response**: Detected attempts raise `ValidationError` and are logged

### SQL Injection Protection (DDL Output)

- **Forbidden patterns**: Regex detection for DML (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`), dangerous DDL (`ALTER DATABASE`, `CREATE USER`, `GRANT`), transaction control, `COPY`, `EXEC`
- **Statement allowlist**: Only `CREATE TABLE`, `CREATE INDEX`, `COMMENT ON`, `ALTER TABLE` (with `ADD CONSTRAINT/COLUMN`) allowed
- **Parsing**: Generated SQL parsed with `sqlparse` for structural validation
- **Post-generation validation**: Runs after LLM generation, before saving

### Path Safety

```python
# In config.py
def resolve_output_dir(self, cwd: Path) -> Path:
    output_dir = self.output_dir
    if not output_dir.is_absolute():
        output_dir = cwd / output_dir
    return output_dir.resolve()  # Resolves symlinks, normalizes

# Usage in output.py
output_dir = settings.resolve_output_dir(Path.cwd())
# Ensure output_dir is within cwd (optional stricter check)
if not output_dir.is_relative_to(Path.cwd()):
    raise OutputError("Output directory must be within working directory")
```

### Secret Handling

- `SecretStr` from Pydantic for all API keys
- Never logged (replaced with `***` in config display)
- Not included in model dumps: `model_dump(exclude={'groq_api_key', ...})`
- Only passed to provider SDK at call time

### SSRF Protection

- `HttpUrl` type validates Ollama URL format
- Default points to localhost
- `follow_redirects=True` with status check on final response

### Rate Limiting

- CLI `design` command limited to 5 requests per minute (in-memory, per process)
- Prevents abuse and excessive LLM API costs

### Audit Logging

Security events logged to `./logs/security.log`:
- Prompt injection attempts (pattern matched, input logged)
- SQL injection attempts in generated DDL (pattern matched, DDL logged)
- Input validation failures

Log format: `timestamp | event_type | detail | input_sample`

### Dependency Security

- `uv lock` generates `uv.lock` with hashes
- `pip-audit` in CI (planned)
- Dependabot for automated updates
- Minimal dependencies (no unnecessary packages)

## Secure Deployment

### Docker

- Non-root user (`appuser`)
- Read-only root filesystem (optional)
- No secrets in image (passed via env at runtime)
- Health checks for Ollama

### CI/CD

- No secrets in repository
- PyPI publishing via trusted publisher (OIDC)
- Container signing (cosign, planned)
- SBOM generation (planned)

## Reporting Vulnerabilities

Report security issues privately to security@example.com (or GitHub Security Advisories).

Do not open public issues for security vulnerabilities.

## Checklist for Releases

- [ ] `pip-audit` passes
- [ ] `uv lock --check` passes
- [ ] No secrets in codebase (`grep -r "sk-\|ghp_\|Bearer "`)
- [ ] Docker image scanned (`docker scout cves`)
- [ ] SBOM generated
- [ ] Changelog updated