"""DDL node for the database design agent."""

from langchain_core.language_models.chat_models import BaseChatModel

from ..exceptions import ValidationError
from ..models import AgentState
from ..prompts import format_ddl_prompt


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

    sql_clean = sql.strip()
    if sql_clean.startswith("```sql"):
        sql_clean = sql_clean[6:]
    if sql_clean.startswith("```"):
        sql_clean = sql_clean[3:]
    if sql_clean.endswith("```"):
        sql_clean = sql_clean[:-3]

    return {"sql_ddl": sql_clean.strip()}
