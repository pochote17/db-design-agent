"""Dictionary node for the database design agent."""

import sys
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from ..exceptions import ValidationError
from ..models import AgentState, DataDictionaryEntry, DatabaseSchema
from ..prompts import format_dictionary_prompt


def dictionary_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Generate data dictionary from database schema."""
    print(f"DEBUG: dictionary_node database_schema type: {type(state.database_schema)}", file=sys.stderr)
    if state.database_schema is None:
        raise ValidationError("Database schema not available", "database_schema")

    # Pass DatabaseSchema object to format_dictionary_prompt
    messages = format_dictionary_prompt(state.database_schema)

    parser = JsonOutputParser(pydantic_object=list[DataDictionaryEntry])

    try:
        chain = llm | parser
        result = chain.invoke(messages)
    except Exception as e:
        print(f"DEBUG: dictionary_node error: {e}", file=sys.stderr)
        raise ValidationError(f"Failed to parse dictionary output: {e}") from e

    if isinstance(result, list):
        # Normalize list fields to strings before validation
        normalized_entries = []
        for item in result:
            if isinstance(item, dict):
                entry = dict(item)
                print(f"DEBUG: entry before normalize: {entry}", file=sys.stderr)
                if isinstance(entry.get("constraints"), list):
                    entry["constraints"] = ", ".join(str(c) for c in entry["constraints"] if c is not None)
                if isinstance(entry.get("example_values"), list):
                    entry["example_values"] = ", ".join(str(v) for v in entry["example_values"] if v is not None)
                # Convert None/bool example_values to string
                if entry.get("example_values") is None:
                    entry["example_values"] = ""
                elif isinstance(entry.get("example_values"), bool):
                    entry["example_values"] = str(entry["example_values"]).lower()
                # Ensure required fields exist
                if not entry.get("table") or not entry.get("column") or not entry.get("business_meaning") or not entry.get("data_type"):
                    print(f"DEBUG: Skipping incomplete entry: {entry}", file=sys.stderr)
                    continue
                # Convert boolean constraints to string
                if isinstance(entry.get("constraints"), bool):
                    entry["constraints"] = str(entry["constraints"]).lower()
                print(f"DEBUG: entry after normalize: {entry}", file=sys.stderr)
                normalized_entries.append(entry)
            else:
                normalized_entries.append(item)
        entries = [DataDictionaryEntry.model_validate(item) if isinstance(item, dict) else item for item in normalized_entries]
    else:
        raise ValidationError("Invalid dictionary output structure")

    return {"data_dictionary": entries}