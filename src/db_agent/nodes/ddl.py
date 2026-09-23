"""DDL node for the database design agent."""

from langchain_core.language_models.chat_models import BaseChatModel

from ..exceptions import ValidationError
from ..models import AgentState
from ..prompts import format_ddl_prompt
from ..security import validate_ddl_output


def ddl_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Generate SQL DDL from database schema."""
    if state.database_schema is None:
        raise ValidationError("Database schema not available", "database_schema")

    messages = format_ddl_prompt(state.database_schema)

    try:
        response = llm.invoke(messages)
        sql = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        raise ValidationError(f"Failed to generate DDL: {e}") from e

    if not sql or not sql.strip():
        raise ValidationError("Empty DDL output")

    # Validate DDL for SQL injection and forbidden patterns
    sql_clean = validate_ddl_output(sql)

    return {"sql_ddl": sql_clean}