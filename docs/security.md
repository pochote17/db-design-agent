# Security

## Threat Model

db-design-agent is a CLI tool that:
- Accepts user-provided business context (text input)
- Calls external LLM APIs or local Ollama
- Stores embeddings in local ChromaDB
- Writes output files to local filesystem

### Attack Vectors

1. **Prompt Injection**: Malicious context attempting to alter agent behavior
2. **Path Traversal**: Output directory manipulation to write outside intended location
3. **Secret Exposure**: API keys leaked in logs, errors, or output files
4. **SSRF**: Ollama base URL pointing to internal services
5. **Dependency Confusion**: Malicious packages in supply chain

## Mitigations

### Input Validation

- Business context: Plain text, no markup interpretation
- Pydantic models validate all structured data
- `extra="forbid"` prevents unexpected fields

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
- Future: allowlist configuration for production

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