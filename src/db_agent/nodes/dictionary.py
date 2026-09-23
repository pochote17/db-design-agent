"""Dictionary node for the database design agent."""

import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from ..exceptions import ValidationError
from ..models import AgentState, DataDictionaryEntry
from ..prompts import format_dictionary_prompt
from ..security import sanitize_for_prompt


def dictionary_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Generate data dictionary from database schema."""
    if state.database_schema is None:
        raise ValidationError("Database schema not available", "database_schema")

    # Sanitize schema for safe inclusion in prompt
    safe_schema = sanitize_for_prompt(
        json.dumps(state.database_schema.model_dump(), indent=2)
    )
    messages = format_dictionary_prompt(safe_schema)

    parser = JsonOutputParser(pydantic_object=list[DataDictionaryEntry])

    try:
        chain = llm | parser
        result = chain.invoke(messages)
    except Exception as e:
        raise ValidationError(f"Failed to parse dictionary output: {e}") from e

    if not isinstance(result, list):
        raise ValidationError("Dictionary output must be a list")

    try:
        entries = [DataDictionaryEntry.model_validate(item) for item in result]
    except Exception as e:
        raise ValidationError(f"Dictionary entry validation failed: {e}") from e

    return {"data_dictionary": entries}