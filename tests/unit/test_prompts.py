"""Unit tests for prompt templates."""

from db_agent.models import Column, DatabaseSchema, Table
from db_agent.prompts import (
    DDL_SYSTEM_PROMPT,
    DESIGN_SYSTEM_PROMPT,
    DICTIONARY_SYSTEM_PROMPT,
    format_ddl_prompt,
    format_design_prompt,
    format_dictionary_prompt,
)


def test_format_design_prompt() -> None:
    """Test design prompt formatting."""
    messages = format_design_prompt("Test context", "Test patterns")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Test context" in messages[1]["content"]
    assert "Test patterns" in messages[1]["content"]


def test_format_dictionary_prompt() -> None:
    """Test dictionary prompt formatting."""
    schema = DatabaseSchema(
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", type="UUID", primary_key=True),
                ],
            )
        ]
    )
    messages = format_dictionary_prompt(schema)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "users" in messages[1]["content"]


def test_format_ddl_prompt() -> None:
    """Test DDL prompt formatting."""
    schema = DatabaseSchema(
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", type="UUID", primary_key=True),
                ],
            )
        ]
    )
    messages = format_ddl_prompt(schema)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "users" in messages[1]["content"]


def test_system_prompts_not_empty() -> None:
    """Test all system prompts are defined."""
    assert len(DESIGN_SYSTEM_PROMPT) > 0
    assert len(DICTIONARY_SYSTEM_PROMPT) > 0
    assert len(DDL_SYSTEM_PROMPT) > 0
