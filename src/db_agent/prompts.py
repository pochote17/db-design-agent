"""Prompt templates for the database design agent."""

import json

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


# Interactive Mode Prompts

QUESTIONS_SYSTEM_PROMPT = """You are an expert database architect. Your task is to ask clarifying questions to better understand the business context before designing a database schema.

You will receive:
1. The original business context
2. Reference patterns from similar domains
3. Previous questions and answers (if any)

Your goal: Generate 3-4 specific, actionable questions that will significantly improve the schema design.

RULES:
- Mix question types: multiple choice, open-ended, yes/no
- Focus on: entities, relationships, constraints, scale, compliance, edge cases
- Questions must be specific to the business context, not generic
- Avoid questions already answered in context or previous rounds
- Return ONLY valid JSON array of question objects

RETURN JSON WITH THIS EXACT STRUCTURE:
[
  {{
    "id": "q1",
    "type": "multiple_choice",
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C"],
    "reasoning": "Why this matters for schema design"
  }},
  {{
    "id": "q2",
    "type": "open_ended",
    "question": "Question text?",
    "reasoning": "Why this matters for schema design"
  }},
  {{
    "id": "q3",
    "type": "yes_no",
    "question": "Question text?",
    "reasoning": "Why this matters for schema design"
  }}
]"""

QUESTIONS_USER_PROMPT = """ORIGINAL BUSINESS CONTEXT:
{context}

REFERENCE PATTERNS:
{patterns}

{history_section}

CURRENT ROUND: {round_number} of 3

Generate 3-4 clarifying questions for this round. Return ONLY the JSON array."""


ANSWER_PROCESSING_SYSTEM_PROMPT = """You are an expert database architect. Process the user's answers to clarifying questions and produce an enriched business context that incorporates all the information gathered.

You will receive:
1. Original business context
2. All questions and answers from all rounds
3. Reference patterns

Your task: Create a comprehensive enriched context that merges the original context with all answers, resolving any conflicts and adding relevant details for schema design.

Return ONLY the enriched context as plain text. No JSON, no markdown."""

ANSWER_PROCESSING_USER_PROMPT = """ORIGINAL BUSINESS CONTEXT:
{context}

ALL QUESTIONS AND ANSWERS:
{qa_section}

REFERENCE PATTERNS:
{patterns}

Create an enriched business context incorporating all answers. Return as plain text."""


READINESS_SYSTEM_PROMPT = """You are an expert database architect. Determine if you have enough information to design a complete, accurate database schema.

You will receive:
1. Enriched business context (original + all answers)
2. Reference patterns
3. Number of clarification rounds completed (max 3)

Evaluate if:
- Core entities and relationships are clear
- Key constraints and requirements are understood
- Scale, compliance, and edge cases are addressed
- Remaining ambiguity is minimal

Return ONLY a JSON object with:
{{
  "is_ready": true/false,
  "reasoning": "Explanation of why ready or not ready"
}}"""

READINESS_USER_PROMPT = """ENRICHED BUSINESS CONTEXT:
{enriched_context}

REFERENCE PATTERNS:
{patterns}

ROUNDS COMPLETED: {rounds_completed} of 3

Is the information sufficient to design a complete, accurate database schema? Return ONLY the JSON object."""


def format_design_prompt(context: str, patterns: str) -> list[dict[str, str]]:
    """Format the design prompt messages."""
    return [
        {"role": "system", "content": DESIGN_SYSTEM_PROMPT},
        {"role": "user", "content": DESIGN_USER_PROMPT.format(context=context, patterns=patterns)},
    ]


def format_dictionary_prompt(schema: DatabaseSchema) -> list[dict[str, str]]:
    """Format the dictionary prompt messages."""
    return [
        {"role": "system", "content": DICTIONARY_SYSTEM_PROMPT},
        {"role": "user", "content": DICTIONARY_USER_PROMPT.format(schema=json.dumps(schema.model_dump(), indent=2))},
    ]


def format_ddl_prompt(schema: DatabaseSchema) -> list[dict[str, str]]:
    """Format the DDL prompt messages."""
    return [
        {"role": "system", "content": DDL_SYSTEM_PROMPT},
        {"role": "user", "content": DDL_USER_PROMPT.format(schema=json.dumps(schema.model_dump(), indent=2))},
    ]


def format_questions_prompt(context: str, patterns: str, history: list[dict[str, str]], round_number: int) -> list[dict[str, str]]:
    """Format the questions generation prompt messages."""
    history_section = ""
    if history:
        history_lines = ["PREVIOUS QUESTIONS AND ANSWERS:"]
        for item in history:
            history_lines.append(f"Q: {item['question']}")
            history_lines.append(f"A: {item['answer']}")
        history_section = "\n".join(history_lines)
    else:
        history_section = "PREVIOUS QUESTIONS AND ANSWERS: None (first round)"

    return [
        {"role": "system", "content": QUESTIONS_SYSTEM_PROMPT},
        {"role": "user", "content": QUESTIONS_USER_PROMPT.format(
            context=context,
            patterns=patterns,
            history_section=history_section,
            round_number=round_number
        )},
    ]


def format_answer_processing_prompt(context: str, qa_pairs: list[dict[str, str]], patterns: str) -> list[dict[str, str]]:
    """Format the answer processing prompt messages."""
    qa_lines = []
    for i, qa in enumerate(qa_pairs, 1):
        qa_lines.append(f"Round {qa.get('round', i)}:")
        qa_lines.append(f"  Q: {qa['question']}")
        qa_lines.append(f"  A: {qa['answer']}")
    qa_section = "\n".join(qa_lines)

    return [
        {"role": "system", "content": ANSWER_PROCESSING_SYSTEM_PROMPT},
        {"role": "user", "content": ANSWER_PROCESSING_USER_PROMPT.format(
            context=context,
            qa_section=qa_section,
            patterns=patterns
        )},
    ]


def format_readiness_prompt(enriched_context: str, patterns: str, rounds_completed: int) -> list[dict[str, str]]:
    """Format the readiness check prompt messages."""
    return [
        {"role": "system", "content": READINESS_SYSTEM_PROMPT},
        {"role": "user", "content": READINESS_USER_PROMPT.format(
            enriched_context=enriched_context,
            patterns=patterns,
            rounds_completed=rounds_completed
        )},
    ]
