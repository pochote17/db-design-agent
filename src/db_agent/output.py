"""Output formatting and file saving for the database design agent."""

import json
from pathlib import Path
from typing import Literal

from .models import AgentState, DatabaseSchema, DataDictionaryEntry

OutputFormat = Literal["json", "sql", "md", "all"]


def format_schema_json(schema: DatabaseSchema) -> str:
    """Format schema as JSON."""
    return schema.model_dump_json(indent=2, exclude_none=True)


def format_dictionary_md(entries: list[DataDictionaryEntry]) -> str:
    """Format data dictionary as Markdown table."""
    if not entries:
        return "# Data Dictionary\n\nNo entries."

    lines = ["# Data Dictionary\n"]
    lines.append("| Table | Column | Business Meaning | Data Type | Constraints | Example Values |")
    lines.append("|-------|--------|------------------|-----------|-------------|----------------|")

    for entry in entries:
        lines.append(
            f"| {entry.table} | {entry.column} | {entry.business_meaning} | "
            f"{entry.data_type} | {entry.constraints} | {entry.example_values} |"
        )

    return "\n".join(lines)


def format_dictionary_json(entries: list[DataDictionaryEntry]) -> str:
    """Format data dictionary as JSON."""
    return json.dumps([e.model_dump() for e in entries], indent=2, ensure_ascii=False)


def save_outputs(
    state: AgentState,
    output_dir: Path,
    formats: list[OutputFormat] = ["json", "sql", "md"],
) -> dict[str, Path]:
    """Save all outputs to files. Returns mapping of format to file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = {}

    if "json" in formats or "all" in formats:
        schema_path = output_dir / "schema.json"
        schema_path.write_text(format_schema_json(state.database_schema), encoding="utf-8")
        saved["json"] = schema_path

        dict_path = output_dir / "dictionary.json"
        dict_path.write_text(format_dictionary_json(state.data_dictionary), encoding="utf-8")
        saved["dictionary_json"] = dict_path

    if "sql" in formats or "all" in formats:
        sql_path = output_dir / "schema.sql"
        sql_path.write_text(state.sql_ddl, encoding="utf-8")
        saved["sql"] = sql_path

    if "md" in formats or "all" in formats:
        md_path = output_dir / "dictionary.md"
        md_path.write_text(format_dictionary_md(state.data_dictionary), encoding="utf-8")
        saved["md"] = md_path

    return saved


def print_results(state: AgentState, verbose: bool = False) -> None:
    """Print results to stdout."""
    print("=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)
    if state.database_schema:
        print(format_schema_json(state.database_schema))
    else:
        print("No schema generated")

    print("\n" + "=" * 60)
    print("DATA DICTIONARY")
    print("=" * 60)
    print(format_dictionary_md(state.data_dictionary))

    print("\n" + "=" * 60)
    print("SQL DDL (PostgreSQL)")
    print("=" * 60)
    print(state.sql_ddl or "No DDL generated")

    if verbose:
        print("\n" + "=" * 60)
        print("RELEVANT PATTERNS")
        print("=" * 60)
        for i, pattern in enumerate(state.relevant_patterns, 1):
            print(f"\n--- Pattern {i} ---")
            print(pattern[:500] + ("..." if len(pattern) > 500 else ""))
