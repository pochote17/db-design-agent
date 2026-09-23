"""Prompt templates for the database design agent."""

from .models import DatabaseSchema

DESIGN_SYSTEM_PROMPT = """You are an expert database architect. Design a complete relational database schema based on the business context and reference patterns.

Return ONLY valid JSON matching the exact structure specified. No additional text, no markdown, no explanations."""

DESIGN_USER_PROMPT = """BUSINESS CONTEXT:
{context}

REFERENCE PATTERNS:
{patterns}

INSTRUCTIONS:
1. Identify main entities and their attributes
2. Define relationships and cardinalities
3. Apply appropriate normalization (typically 3NF)
4. Consider SCD Type 2 for data that changes with history
5. Include recommended indexes
6. Use conventions: snake_case, PK=id, FK=table_id, timestamptz
7. PostgreSQL types: UUID, numeric(12,2), jsonb, citext, enum

RETURN JSON WITH THIS EXACT STRUCTURE:
{{
  "tables": [
    {{
      "name": "table_name",
      "description": "business description",
      "columns": [
        {{
          "name": "column_name",
          "type": "data_type",
          "nullable": false,
          "primary_key": true,
          "foreign_key": null,
          "description": "column description",
          "default": null
        }}
      ],
      "indexes": [
        {{
          "name": "idx_table_column",
          "columns": ["column"],
          "unique": false,
          "where": null
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "source_table": "table1",
      "source_column": "id",
      "target_table": "table2",
      "target_column": "table1_id",
      "cardinality": "1:N"
    }}
  ]
}}"""


DICTIONARY_SYSTEM_PROMPT = """You are a data dictionary generator. Create a technical-business data dictionary for the given database schema.

Return ONLY valid JSON array of objects. No additional text."""

DICTIONARY_USER_PROMPT = """DATABASE SCHEMA:
{schema}

For each column in each table, provide:
- table: table name
- column: column name
- business_meaning: what this field represents in business terms
- data_type: PostgreSQL data type
- constraints: constraints (PK, FK, NOT NULL, UNIQUE, CHECK, etc.)
- example_values: realistic example values

Return as JSON array."""


DDL_SYSTEM_PROMPT = """You are a PostgreSQL DDL generator. Generate complete, production-ready SQL DDL for the given schema.

Return ONLY the SQL statements. No markdown, no explanations, no additional text."""

DDL_USER_PROMPT = """DATABASE SCHEMA:
{schema}

REQUIREMENTS:
- CREATE TABLE with all constraints (PK, FK, NOT NULL, UNIQUE, CHECK)
- CREATE INDEX for declared indexes
- Types: UUID, timestamptz, numeric(12,2), jsonb, citext, enum
- DEFAULT gen_random_uuid() for PK UUID
- DEFAULT now() for created_at
- ON DELETE RESTRICT/SET NULL/CASCADE as appropriate
- COMMENT ON for tables and columns
- Proper PostgreSQL syntax

Return ONLY the SQL."""


def format_design_prompt(context: str, patterns: str) -> list[dict[str, str]]:
    """Format the design prompt messages."""
    return [
        {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
        {"role": "user", "content": DESIGN_USER_PROMPT.format(context=context, patterns=patterns)},
    ]


def format_dictionary_prompt(schema: DatabaseSchema) -> list[dict[str, str]]:
    """Format the dictionary prompt messages."""
    import json
    return [
        {"role": "system", "content": DICTIONARY_SYSTEM_PROMPT},
        {"role": "user", "content": DICTIONARY_USER_PROMPT.format(schema=json.dumps(schema.model_dump(), indent=2))},
    ]


def format_ddl_prompt(schema: DatabaseSchema) -> list[dict[str, str]]:
    """Format the DDL prompt messages."""
    import json
    return [
        {"role": "system", "content": DDL_SYSTEM_PROMPT},
        {"role": "user", "content": DDL_USER_PROMPT.format(schema=json.dumps(schema.model_dump(), indent=2))},
    ]
