"""DDL node for the database design agent."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from ..exceptions import ValidationError, ValidationErrorCodes
from ..models import AgentState
from ..prompts import DDL_SYSTEM_PROMPT, DDL_USER_PROMPT
from ..security import validate_ddl_output


def ddl_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Generate SQL DDL from database schema with retry logic."""
    if state.database_schema is None:
        raise ValidationError("Database schema not available", "database_schema")

    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            if attempt == 0:
                # First attempt: use structured prompts
                messages = [
                    SystemMessage(content=DDL_SYSTEM_PROMPT),
                    HumanMessage(content=DDL_USER_PROMPT.format(
                        schema=state.database_schema.model_dump_json(indent=2)
                    )),
                ]
            else:
                # Retry: provide error feedback to LLM
                messages = [
                    SystemMessage(content=DDL_SYSTEM_PROMPT + "\n\nPREVIOUS ERROR: " + str(last_error) + "\nFix the SQL and return ONLY valid statements."),
                    HumanMessage(content=DDL_USER_PROMPT.format(
                        schema=state.database_schema.model_dump_json(indent=2)
                    )),
                ]

            response = llm.invoke(messages)
            sql = response.content if hasattr(response, "content") else str(response)

            # DEBUG - print to stderr
            import sys
            print(f"DDL attempt {attempt + 1} raw output: {repr(sql)}", file=sys.stderr)

            if not sql or not sql.strip():
                raise ValidationError("Empty DDL output")

            # Validate DDL for SQL injection and forbidden patterns
            sql_clean = validate_ddl_output(sql)

            print(f"DDL cleaned output: {repr(sql_clean)}", file=sys.stderr)
            return {"sql_ddl": sql_clean}

        except ValidationError as e:
            last_error = e
            if e.code in (ValidationErrorCodes.SQL_PARSE_FAILED,
                          ValidationErrorCodes.FORBIDDEN_SQL_PATTERN,
                          ValidationErrorCodes.DISALLOWED_SQL_STATEMENT,
                          ValidationErrorCodes.DISALLOWED_ALTER_TABLE):
                if attempt < max_retries:
                    continue
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue
            raise ValidationError(f"Failed to generate DDL: {e}") from e

    raise ValidationError(f"Failed to generate valid DDL after {max_retries + 1} attempts: {last_error}")