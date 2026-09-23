"""CLI for db-design-agent."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .config import LLMProvider, Settings, get_settings
from .exceptions import AgentError, ConfigurationError
from .graph import run_agent
from .output import OutputFormat, print_results, save_outputs

app = typer.Typer(
    name="db-design-agent",
    help="AI agent for database schema design from business context",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)


def _get_format_list(format_str: str) -> list[OutputFormat]:
    """Parse format string into list."""
    if format_str == "all":
        return ["json", "sql", "md"]
    return [f.strip() for f in format_str.split(",") if f.strip() in ("json", "sql", "md")]


def _validate_provider_config(provider: LLMProvider, settings: Settings) -> None:
    """Validate that required configuration exists for provider."""
    if provider == LLMProvider.GROQ and not settings.groq_api_key:
        raise ConfigurationError(
            "GROQ_API_KEY required for Groq provider. "
            "Set DB_AGENT_GROQ_API_KEY in environment or .env file."
        )
    if provider == LLMProvider.OPENAI and not settings.openai_api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY required for OpenAI provider. "
            "Set DB_AGENT_OPENAI_API_KEY in environment or .env file."
        )
    if provider == LLMProvider.ANTHROPIC and not settings.anthropic_api_key:
        raise ConfigurationError(
            "ANTHROPIC_API_KEY required for Anthropic provider. "
            "Set DB_AGENT_ANTHROPIC_API_KEY in environment or .env file."
        )
    if provider == LLMProvider.OLLAMA:
        pass


@app.command()
def design(
    context: str = typer.Argument(..., help="Business context description"),
    provider: LLMProvider | None = typer.Option(
        None, "--provider", "-p", help="LLM provider (overrides config)"
    ),
    model: str | None = typer.Option(
        None, "--model", "-m", help="Model name (uses provider default if not specified)"
    ),
    output_dir: Path = typer.Option(
        Path("./output"), "--output", "-o", help="Output directory"
    ),
    format: str = typer.Option(
        "all", "--format", "-f", help="Output formats: json,sql,md,all"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show additional details"
    ),
    config_file: Path | None = typer.Option(
        None, "--config", "-c", help="Path to .env config file"
    ),
) -> None:
    """Design database schema from business context."""
    try:
        settings = get_settings(config_file)

        # Override provider/model from CLI if provided
        if provider or model:
            settings = Settings(
                llm_provider=provider or settings.llm_provider,
                llm_model=model or settings.llm_model,
                groq_api_key=settings.groq_api_key,
                openai_api_key=settings.openai_api_key,
                anthropic_api_key=settings.anthropic_api_key,
                ollama_base_url=settings.ollama_base_url,
                embedding_model=settings.embedding_model,
                chroma_persist_dir=settings.chroma_persist_dir,
                log_level=settings.log_level,
                output_dir=output_dir,
                _env_file=config_file,
            )

        # Validate using settings.llm_provider (not CLI option)
        _validate_provider_config(settings.llm_provider, settings)

        console.print(f"[bold]Provider:[/bold] {settings.llm_provider.value}")
        console.print(f"[bold]Model:[/bold] {settings.llm_model}")
        console.print(f"[bold]Context:[/bold] {context[:100]}{'...' if len(context) > 100 else ''}")

        with console.status("[bold green]Analyzing and designing...[/bold green]"):
            import asyncio
            state = asyncio.run(run_agent(context, settings))

        print_results(state, verbose)

        formats = _get_format_list(format)
        saved = save_outputs(state, output_dir, formats)

        console.print("\n[bold green]Files saved:[/bold green]")
        for fmt, path in saved.items():
            console.print(f"  {fmt}: {path}")

    except AgentError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e.message}")
        if e.code == "CONFIG_ERROR":
            err_console.print("[yellow]Run 'db-design-agent config --wizard' to configure.[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            import traceback
            err_console.print(traceback.format_exc())
        sys.exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    wizard: bool = typer.Option(False, "--wizard", help="Run interactive configuration wizard"),
    provider: LLMProvider | None = typer.Option(
        None, "--provider", "-p", help="Set default provider"
    ),
    model: str | None = typer.Option(None, "--model", "-m", help="Set default model"),
) -> None:
    """Manage configuration."""
    settings = get_settings()

    if show:
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("LLM Provider", settings.llm_provider.value)
        table.add_row("LLM Model", settings.llm_model)
        table.add_row("Groq API Key", "***" if settings.groq_api_key else "Not set")
        table.add_row("OpenAI API Key", "***" if settings.openai_api_key else "Not set")
        table.add_row("Anthropic API Key", "***" if settings.anthropic_api_key else "Not set")
        table.add_row("Ollama Base URL", str(settings.ollama_base_url))
        table.add_row("Embedding Model", settings.embedding_model)
        table.add_row("ChromaDB Dir", str(settings.chroma_persist_dir))
        table.add_row("Output Dir", str(settings.output_dir))
        table.add_row("Log Level", settings.log_level)

        console.print(table)
        return

    if wizard:
        _run_config_wizard()
        return

    if provider or model:
        err_console.print("[yellow]Use --wizard to interactively update config, or set env vars directly.[/yellow]")
        raise typer.Exit(1)

    err_console.print("[yellow]Use --show to view config, or --wizard to configure interactively.[/yellow]")


def _run_config_wizard() -> None:
    """Interactive configuration wizard."""
    console.print("[bold]db-design-agent Configuration Wizard[/bold]\n")

    provider_choices = [p.value for p in LLMProvider]
    provider = Prompt.ask(
        "Select LLM provider",
        choices=provider_choices,
        default="ollama",
    )

    settings = get_settings()
    default_model = settings.get_default_model(LLMProvider(provider))
    model = Prompt.ask("Model name", default=default_model)

    env_lines = []

    if provider == "groq":
        api_key = Prompt.ask("GROQ API Key (get free at console.groq.com)", password=True)
        if api_key:
            env_lines.append(f"DB_AGENT_GROQ_API_KEY={api_key}")
    elif provider == "openai":
        api_key = Prompt.ask("OpenAI API Key", password=True)
        if api_key:
            env_lines.append(f"DB_AGENT_OPENAI_API_KEY={api_key}")
    elif provider == "anthropic":
        api_key = Prompt.ask("Anthropic API Key", password=True)
        if api_key:
            env_lines.append(f"DB_AGENT_ANTHROPIC_API_KEY={api_key}")

    env_lines.append(f"DB_AGENT_LLM_PROVIDER={provider}")
    env_lines.append(f"DB_AGENT_LLM_MODEL={model}")

    # Write to BOTH locations: project .env (priority) and user config
    project_env = Path.cwd() / ".env"
    user_env = Path.home() / ".config" / "db-design-agent" / ".env"
    user_env.parent.mkdir(parents=True, exist_ok=True)

    # Read existing project .env if exists
    if project_env.exists():
        existing = project_env.read_text(encoding="utf-8").strip()
        if existing:
            env_lines.insert(0, existing)

    project_env.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    console.print(f"\n[green]Configuration saved to {project_env}[/green]")

    # Also save to user config directory
    user_env.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    console.print(f"[green]Configuration also saved to {user_env}[/green]")

    console.print("\n[yellow]Settings will be picked up automatically on next run.[/yellow]")


@app.command()
def doctor(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed checks"),
) -> None:
    """Check system health and configuration."""
    console.print("[bold]db-design-agent Health Check[/bold]\n")

    settings = get_settings()
    checks = []

    # Config check
    try:
        _validate_provider_config(settings.llm_provider, settings)
        checks.append(("Configuration", "OK", f"Provider: {settings.llm_provider.value}"))
    except ConfigurationError as e:
        checks.append(("Configuration", "FAIL", str(e)))

    # Ollama check
    if settings.llm_provider == LLMProvider.OLLAMA or settings.embedding_provider.value == "ollama":
        try:
            import httpx
            response = httpx.get(str(settings.ollama_base_url) + "/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                checks.append(("Ollama", "OK", f"Running, {len(models)} models available"))
                if verbose:
                    checks.append(("", "", f"Models: {', '.join(model_names[:5])}{'...' if len(model_names) > 5 else ''}"))
            else:
                checks.append(("Ollama", "WARN", f"HTTP {response.status_code}"))
        except Exception as e:
            checks.append(("Ollama", "FAIL", f"Connection failed: {e}"))

    # ChromaDB directory
    chroma_dir = settings.resolve_chroma_dir(Path.cwd())
    if chroma_dir.exists():
        checks.append(("ChromaDB", "OK", f"Directory exists: {chroma_dir}"))
    else:
        checks.append(("ChromaDB", "WARN", f"Directory will be created: {chroma_dir}"))

    # Output directory
    output_dir = settings.resolve_output_dir(Path.cwd())
    if output_dir.exists():
        checks.append(("Output Dir", "OK", f"Directory exists: {output_dir}"))
    else:
        checks.append(("Output Dir", "WARN", f"Directory will be created: {output_dir}"))

    # Dependencies
    deps = [
        ("langgraph", "langgraph"),
        ("langchain-core", "langchain_core"),
        ("langchain-ollama", "langchain_ollama"),
        ("langchain-chroma", "langchain_chroma"),
        ("chromadb", "chromadb"),
        ("pydantic", "pydantic"),
        ("typer", "typer"),
        ("rich", "rich"),
    ]

    for name, module in deps:
        try:
            __import__(module)
            checks.append((f"Dependency: {name}", "OK", "Installed"))
        except ImportError:
            checks.append((f"Dependency: {name}", "FAIL", "Not installed"))

    # Print results
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    for component, status, details in checks:
        status_style = "green" if status == "OK" else ("yellow" if status == "WARN" else "red")
        table.add_row(component, f"[{status_style}]{status}[/{status_style}]", details)

    console.print(table)

    # Summary
    failed = sum(1 for _, s, _ in checks if s == "FAIL")
    if failed:
        console.print(f"\n[bold red]{failed} check(s) failed[/bold red]")
        sys.exit(1)
    else:
        console.print("\n[bold green]All checks passed[/bold green]")


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    console.print(f"db-design-agent version {__version__}")


def main() -> None:
    """Entry point for console script."""
    app()


if __name__ == "__main__":
    main()
