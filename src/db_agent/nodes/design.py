"""Design node for the database design agent."""

import sys
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from ..exceptions import ValidationError
from ..models import AgentState, DatabaseSchema
from ..prompts import format_design_prompt
from ..security import sanitize_for_prompt


def design_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Design database schema from context and patterns."""
    if not state.business_context.strip():
        raise ValidationError("Business context is empty", "business_context")

    if not state.relevant_patterns:
        raise ValidationError("No relevant patterns retrieved", "relevant_patterns")

    # Sanitize patterns for safe inclusion in prompt
    safe_patterns = "\n\n".join(sanitize_for_prompt(p) for p in state.relevant_patterns)
    messages = format_design_prompt(state.business_context, safe_patterns)

    parser = JsonOutputParser(pydantic_object=DatabaseSchema)

    try:
        print("DEBUG: Calling LLM for design_node", file=sys.stderr)
        chain = llm | parser
        result = chain.invoke(messages)
        print(f"DEBUG: design_node got result type: {type(result)}", file=sys.stderr)
    except Exception as e:
        print(f"DEBUG: design_node error: {e}", file=sys.stderr)
        raise ValidationError(f"Failed to parse design output: {e}") from e

    # Handle both dict and DatabaseSchema object
    if isinstance(result, DatabaseSchema):
        schema = result
    elif isinstance(result, dict):
        try:
            schema = DatabaseSchema.model_validate(result)
        except Exception as e:
            raise ValidationError(f"Schema validation failed: {e}") from e
    else:
        raise ValidationError(f"Invalid design output type: {type(result)}")

    return {"database_schema": schema}