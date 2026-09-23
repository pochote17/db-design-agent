"""Security utilities for db-design-agent: input sanitization, prompt injection detection, SQL validation, and audit logging."""

import logging
import re
from enum import Enum
from pathlib import Path
from typing import Optional

import sqlparse
from sqlparse.tokens import DDL, DML, Keyword

from .exceptions import ValidationError


class SecurityEventType(str, Enum):
    """Types of security events."""
    PROMPT_INJECTION = "prompt_injection"
    SQL_INJECTION = "sql_injection"
    INPUT_VALIDATION = "input_validation"


# Patterns that may indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:previous|prior|above)\s+instructions?",
    r"disregard\s+(?:previous|prior|above)\s+instructions?",
    r"forget\s+(?:previous|prior|above)\s+instructions?",
    r"override\s+(?:previous|prior|above)\s+instructions?",
    r"system\s*:\s*you\s+are\s+now",
    r"you\s+are\s+now\s+(?:a|an)\s+\w+",
    r"pretend\s+to\s+be\s+(?:a|an)\s+\w+",
    r"act\s+as\s+(?:a|an)\s+\w+",
    r"roleplay\s+as\s+(?:a|an)\s+\w+",
    r"simulate\s+(?:a|an)\s+\w+",
    r"ignore\s+the\s+(?:system|security|safety)",
    r"bypass\s+(?:the\s+)?(?:system|security|safety)",
    r"reveal\s+(?:your\s+)?(?:system\s+)?prompt",
    r"show\s+me\s+(?:your\s+)?(?:system\s+)?prompt",
    r"what\s+(?:is|are)\s+(?:your\s+)?(?:system\s+)?prompt",
    r"output\s+(?:your\s+)?(?:system\s+)?prompt",
    r"print\s+(?:your\s+)?(?:system\s+)?prompt",
    r"repeat\s+(?:your\s+)?(?:system\s+)?prompt",
    r"##\s*(?:system|user|assistant)\s*##",
    r"<\|?(?:system|user|assistant)\|?>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"<</SYS>>",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
]

# SQL statements/keywords that are NOT allowed in generated DDL
FORBIDDEN_SQL_PATTERNS = [
    # DML operations
    r"\bDROP\s+(?:TABLE|INDEX|VIEW|DATABASE|SCHEMA|SEQUENCE|FUNCTION|PROCEDURE|TRIGGER)\b",
    r"\bDELETE\s+FROM\b",
    r"\bUPDATE\s+\w+\s+SET\b",
    r"\bINSERT\s+INTO\b",
    r"\bTRUNCATE\s+(?:TABLE\s+)?\w+\b",
    r"\bMERGE\s+INTO\b",
    r"\bREPLACE\s+INTO\b",
    # DDL dangerous
    r"\bALTER\s+(?:DATABASE|SCHEMA|SYSTEM)\b",
    r"\bCREATE\s+(?:DATABASE|SCHEMA|USER|ROLE|FUNCTION|PROCEDURE|TRIGGER|VIEW)\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bALTER\s+TABLE\s+\w+\s+(?:DISABLE|ENABLE)\s+(?:TRIGGER|CONSTRAINT|RULE)\b",
    # Transaction control
    r"\bCOMMIT\b",
    r"\bROLLBACK\b",
    r"\bSAVEPOINT\b",
    r"\bBEGIN\s+(?:TRANSACTION|WORK)?\b",
    # Copy/Import/Export
    r"\bCOPY\b",
    r"\\copy\b",
    # Execution
    r"\bEXEC(?:UTE)?\b",
    r"\bCALL\b",
    # Comments used for injection
    r"/\*.*?\*/",
    r"--\s*$",
    # Multiple statements (potential injection)
    r";\s*(?:DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|GRANT|REVOKE|EXEC|COPY)",
]

# Compile patterns for efficiency
_PROMPT_INJECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS]
_FORBIDDEN_SQL_REGEX = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_SQL_PATTERNS]

# Allowed SQL statement types for generated DDL
ALLOWED_DDL_STATEMENTS = {
    "CREATE TABLE",
    "CREATE INDEX",
    "CREATE UNIQUE INDEX",
    "COMMENT ON",
    "ALTER TABLE",
    # Only ALTER TABLE with ADD CONSTRAINT, ADD COLUMN, ALTER COLUMN
}

# Maximum input lengths
MAX_CONTEXT_LENGTH = 10000
MAX_QUERY_LENGTH = 1000


class SecurityLogger:
    """Audit logger for security events."""

    _instance: Optional["SecurityLogger"] = None
    _logger: logging.Logger | None = None

    def __new__(cls) -> "SecurityLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._logger is not None:
            return

        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)

        self._logger = logging.getLogger("db_design_agent.security")
        self._logger.setLevel(logging.WARNING)
        self._logger.propagate = False

        handler = logging.FileHandler(log_dir / "security.log", encoding="utf-8")
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def log_event(
        self,
        event_type: SecurityEventType,
        detail: str,
        input_sample: str | None = None,
    ) -> None:
        """Log a security event."""
        if self._logger is None:
            return

        msg_parts = [f"{event_type.value} | {detail}"]
        if input_sample:
            # Truncate and sanitize for log
            sample = input_sample[:200].replace("\n", "\\n").replace("\r", "")
            msg_parts.append(f"input: {sample}")

        self._logger.warning(" | ".join(msg_parts))


# Global instance
_security_logger = SecurityLogger()


def get_security_logger() -> SecurityLogger:
    """Get the global security logger instance."""
    return _security_logger


def sanitize_user_input(text: str, max_length: int = MAX_CONTEXT_LENGTH) -> str:
    """Sanitize user input: strip control chars, limit length, normalize whitespace."""
    if not text:
        return ""

    # Remove null bytes and control characters except newline/tab
    text = "".join(
        ch for ch in text
        if ch == "\n" or ch == "\t" or ch == "\r" or ord(ch) >= 32
    )

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"

    return text.strip()


def detect_prompt_injection(text: str) -> str | None:
    """Detect potential prompt injection in text. Returns matched pattern or None."""
    if not text:
        return None

    text_lower = text.lower()
    for pattern_regex in _PROMPT_INJECTION_REGEX:
        if pattern_regex.search(text_lower):
            return pattern_regex.pattern
    return None


def validate_no_prompt_injection(text: str, field_name: str = "input") -> None:
    """Validate text for prompt injection. Raises ValidationError if detected."""
    matched = detect_prompt_injection(text)
    if matched:
        _security_logger.log_event(
            SecurityEventType.PROMPT_INJECTION,
            f"Detected in {field_name}: pattern matched",
            input_sample=text,
        )
        raise ValidationError(
            f"Potential prompt injection detected in {field_name}",
            field=field_name,
        )


def validate_input_length(text: str, field_name: str, max_length: int) -> None:
    """Validate input length."""
    if len(text) > max_length:
        raise ValidationError(
            f"{field_name} exceeds maximum length of {max_length} characters",
            field=field_name,
        )


def validate_ddl_output(sql: str) -> str:
    """
    Validate generated DDL for SQL injection and forbidden patterns.
    Returns cleaned SQL if valid.
    Raises ValidationError if invalid.
    """
    if not sql or not sql.strip():
        raise ValidationError("Empty DDL output")

    # Clean up markdown code fences
    sql_clean = sql.strip()
    if sql_clean.startswith("```sql"):
        sql_clean = sql_clean[6:]
    elif sql_clean.startswith("```"):
        sql_clean = sql_clean[3:]
    if sql_clean.endswith("```"):
        sql_clean = sql_clean[:-3]
    sql_clean = sql_clean.strip()

    # Check for forbidden patterns
    for pattern_regex in _FORBIDDEN_SQL_REGEX:
        match = pattern_regex.search(sql_clean)
        if match:
            _security_logger.log_event(
                SecurityEventType.SQL_INJECTION,
                f"Forbidden pattern matched: {pattern_regex.pattern}",
                input_sample=sql_clean,
            )
            raise ValidationError(
                f"Forbidden SQL pattern detected: {pattern_regex.pattern}",
                field="sql_ddl",
            )

    # Parse with sqlparse and validate statement types
    try:
        parsed = sqlparse.parse(sql_clean)
    except Exception as e:
        raise ValidationError(f"Failed to parse SQL: {e}")

    for statement in parsed:
        if not statement.tokens:
            continue

        # Get statement type
        stmt_type = statement.get_type()
        first_token = None
        for token in statement.flatten():
            if token.ttype is not None and token.ttype in (Keyword, DDL, DML):
                first_token = token.value.upper()
                break

        # Check if statement type is allowed
        stmt_upper = stmt_type.upper() if stmt_type else ""
        if stmt_upper and stmt_upper not in ALLOWED_DDL_STATEMENTS:
            # Also check for ALTER TABLE which is allowed but need to verify content
            if not stmt_upper.startswith("ALTER TABLE"):
                _security_logger.log_event(
                    SecurityEventType.SQL_INJECTION,
                    f"Disallowed statement type: {stmt_type}",
                    input_sample=str(statement)[:200],
                )
                raise ValidationError(
                    f"Disallowed SQL statement type: {stmt_type}",
                    field="sql_ddl",
                )

        # For ALTER TABLE, verify it's only ADD CONSTRAINT/COLUMN
        if stmt_upper.startswith("ALTER TABLE"):
            stmt_str = str(statement).upper()
            if not any(x in stmt_str for x in ["ADD CONSTRAINT", "ADD COLUMN", "ALTER COLUMN"]):
                _security_logger.log_event(
                    SecurityEventType.SQL_INJECTION,
                    "Disallowed ALTER TABLE operation",
                    input_sample=str(statement)[:200],
                )
                raise ValidationError(
                    "Disallowed ALTER TABLE operation (only ADD CONSTRAINT/COLUMN allowed)",
                    field="sql_ddl",
                )

    return sql_clean


def sanitize_for_prompt(text: str) -> str:
    """Sanitize text for safe inclusion in prompt templates."""
    # Escape curly braces to prevent template injection
    text = text.replace("{", "{{").replace("}", "}}")
    # Limit newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def validate_query_input(query: str) -> str:
    """Validate and sanitize query for vector search."""
    if not query or not query.strip():
        return ""

    query = sanitize_user_input(query, MAX_QUERY_LENGTH)
    validate_no_prompt_injection(query, "query")
    return query


def validate_context_input(context: str) -> str:
    """Validate and sanitize business context input."""
    if not context or not context.strip():
        raise ValidationError("Business context cannot be empty", "business_context")

    context = sanitize_user_input(context, MAX_CONTEXT_LENGTH)
    validate_no_prompt_injection(context, "business_context")
    return context