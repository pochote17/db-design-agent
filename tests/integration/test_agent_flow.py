"""Integration tests for the agent flow with mocked LLM."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db_agent.config import LLMProvider, Settings
from db_agent.graph import run_agent
from db_agent.models import (
    AgentState,
    DatabaseSchema,
    DataDictionaryEntry,
)

SAMPLE_SCHEMA = {
    "tables": [
        {
            "name": "users",
            "description": "User accounts",
            "columns": [
                {
                    "name": "id",
                    "type": "UUID",
                    "nullable": False,
                    "primary_key": True,
                    "foreign_key": None,
                    "description": "Unique identifier",
                    "default": "gen_random_uuid()",
                },
                {
                    "name": "email",
                    "type": "citext",
                    "nullable": False,
                    "primary_key": False,
                    "foreign_key": None,
                    "description": "User email",
                    "default": None,
                },
            ],
            "indexes": [
                {"name": "idx_users_email", "columns": ["email"], "unique": True, "where": None}
            ],
        }
    ],
    "relationships": [],
}

SAMPLE_DICTIONARY = [
    {
        "table": "users",
        "column": "id",
        "business_meaning": "Unique identifier for user",
        "data_type": "UUID",
        "constraints": "PRIMARY KEY, NOT NULL",
        "example_values": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    },
    {
        "table": "users",
        "column": "email",
        "business_meaning": "User email for login",
        "data_type": "citext",
        "constraints": "NOT NULL, UNIQUE",
        "example_values": "user@example.com",
    },
]

SAMPLE_DDL = """CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email citext NOT NULL UNIQUE
);

COMMENT ON TABLE users IS 'User accounts';
COMMENT ON COLUMN users.id IS 'Unique identifier';
COMMENT ON COLUMN users.email IS 'User email';
"""


def create_mock_embeddings() -> MagicMock:
    """Create a mock embeddings model that returns proper vectors for any input size."""
    mock = MagicMock()

    def embed_documents(texts):
        return [[0.1] * 768 for _ in texts]

    def embed_query(text):
        return [0.1] * 768

    async def aembed_documents(texts):
        return [[0.1] * 768 for _ in texts]

    async def aembed_query(text):
        return [0.1] * 768

    mock.embed_documents = MagicMock(side_effect=embed_documents)
    mock.embed_query = MagicMock(side_effect=embed_query)
    mock.aembed_documents = AsyncMock(side_effect=aembed_documents)
    mock.aembed_query = AsyncMock(side_effect=aembed_query)
    return mock


@pytest.fixture
def mock_embeddings() -> MagicMock:
    """Create a mock embeddings model."""
    return create_mock_embeddings()


@pytest.fixture
def settings() -> Settings:
    """Test settings with Ollama provider (no API key needed)."""
    return Settings(
        llm_provider=LLMProvider.OLLAMA,
        llm_model="llama3.1:8b",
        ollama_base_url="http://localhost:11434",
        chroma_persist_dir="./test_chroma",
        output_dir="./test_output",
    )


@pytest.mark.asyncio
async def test_build_graph(mock_embeddings: MagicMock, tmp_path: pytest.TempPathFactory) -> None:
    """Test graph compilation."""
    test_settings = Settings(
        llm_provider=LLMProvider.OLLAMA,
        chroma_persist_dir=tmp_path / "chroma",
        output_dir=tmp_path / "output",
    )
    with patch("db_agent.graph.create_embeddings", return_value=mock_embeddings):
        from db_agent.graph import build_graph
        graph = build_graph(test_settings, tmp_path)
        assert graph is not None


@pytest.mark.asyncio
async def test_run_agent_with_mock(
    mock_embeddings: MagicMock,
    tmp_path: pytest.TempPathFactory,
) -> None:
    """Test full agent flow with mocked graph execution."""
    test_settings = Settings(
        llm_provider=LLMProvider.OLLAMA,
        chroma_persist_dir=tmp_path / "chroma",
        output_dir=tmp_path / "output",
    )

    # Create a mock final state
    mock_final_state = AgentState(
        business_context="E-commerce platform with users, products, and orders",
        relevant_patterns=["test pattern"],
        database_schema=DatabaseSchema.model_validate(SAMPLE_SCHEMA),
        data_dictionary=[DataDictionaryEntry.model_validate(d) for d in SAMPLE_DICTIONARY],
        sql_ddl=SAMPLE_DDL,
    )

    with patch("db_agent.graph.create_embeddings", return_value=mock_embeddings):
        with patch("db_agent.graph.build_graph") as mock_build_graph:
            mock_graph = AsyncMock()
            mock_graph.ainvoke = AsyncMock(return_value=mock_final_state)
            mock_build_graph.return_value = mock_graph

            state = await run_agent(
                "E-commerce platform with users, products, and orders",
                test_settings,
                tmp_path,
            )

    assert state.database_schema is not None
    assert len(state.database_schema.tables) == 1
    assert state.database_schema.tables[0].name == "users"
    assert len(state.data_dictionary) == 2
    assert "CREATE TABLE users" in state.sql_ddl


@pytest.mark.asyncio
async def test_agent_state_validation() -> None:
    """Test agent state validation."""
    state = AgentState(business_context="Test")
    assert state.business_context == "Test"


def test_database_schema_model_validation() -> None:
    """Test DatabaseSchema model validates correctly."""
    schema = DatabaseSchema.model_validate(SAMPLE_SCHEMA)
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "users"
    assert schema.tables[0].columns[0].primary_key is True
    assert schema.tables[0].columns[1].nullable is False


def test_data_dictionary_model_validation() -> None:
    """Test DataDictionaryEntry model validates correctly."""
    entries = [DataDictionaryEntry.model_validate(d) for d in SAMPLE_DICTIONARY]
    assert len(entries) == 2
    assert entries[0].table == "users"
    assert entries[1].column == "email"
