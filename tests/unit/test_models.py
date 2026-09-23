"""Unit tests for Pydantic models."""

import pytest

from db_agent.models import (
    AgentState,
    Column,
    DatabaseSchema,
    DataDictionaryEntry,
    Index,
    Relationship,
    Table,
)


def test_column_defaults() -> None:
    """Test column default values."""
    col = Column(name="id", type="UUID")
    assert col.nullable is False
    assert col.primary_key is False
    assert col.foreign_key is None
    assert col.description == ""
    assert col.default is None


def test_column_primary_key() -> None:
    """Test primary key column."""
    col = Column(name="id", type="UUID", primary_key=True, nullable=False)
    assert col.primary_key is True
    assert col.nullable is False


def test_column_foreign_key() -> None:
    """Test foreign key column."""
    col = Column(name="user_id", type="UUID", foreign_key="users.id")
    assert col.foreign_key == "users.id"


def test_index_unique() -> None:
    """Test unique index."""
    idx = Index(name="idx_users_email", columns=["email"], unique=True)
    assert idx.unique is True


def test_index_partial() -> None:
    """Test partial index with WHERE clause."""
    idx = Index(name="idx_active_users", columns=["id"], where="is_active = true")
    assert idx.where == "is_active = true"


def test_table_with_columns() -> None:
    """Test table with multiple columns."""
    table = Table(
        name="users",
        columns=[
            Column(name="id", type="UUID", primary_key=True),
            Column(name="email", type="citext", nullable=False),
            Column(name="created_at", type="timestamptz", default="now()"),
        ],
        description="User accounts",
    )
    assert len(table.columns) == 3
    assert table.columns[0].primary_key is True
    assert table.columns[1].nullable is False


def test_relationship_cardinality() -> None:
    """Test relationship cardinality validation."""
    rel = Relationship(
        source_table="orders",
        source_column="user_id",
        target_table="users",
        target_column="id",
        cardinality="N:1",
    )
    assert rel.cardinality == "N:1"


def test_relationship_invalid_cardinality() -> None:
    """Test invalid cardinality raises error."""
    with pytest.raises(Exception):
        Relationship(
            source_table="orders",
            source_column="user_id",
            target_table="users",
            target_column="id",
            cardinality="INVALID",
        )


def test_database_schema() -> None:
    """Test complete database schema."""
    schema = DatabaseSchema(
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", type="UUID", primary_key=True),
                    Column(name="email", type="citext", nullable=False),
                ],
            ),
            Table(
                name="orders",
                columns=[
                    Column(name="id", type="UUID", primary_key=True),
                    Column(name="user_id", type="UUID", foreign_key="users.id"),
                ],
            ),
        ],
        relationships=[
            Relationship(
                source_table="orders",
                source_column="user_id",
                target_table="users",
                target_column="id",
                cardinality="N:1",
            ),
        ],
    )
    assert len(schema.tables) == 2
    assert len(schema.relationships) == 1


def test_data_dictionary_entry() -> None:
    """Test data dictionary entry."""
    entry = DataDictionaryEntry(
        table="users",
        column="email",
        business_meaning="User's email address for login and notifications",
        data_type="citext",
        constraints="NOT NULL, UNIQUE",
        example_values="john.doe@example.com",
    )
    assert entry.table == "users"
    assert entry.column == "email"


def test_agent_state_defaults() -> None:
    """Test agent state default values."""
    state = AgentState(business_context="Test context")
    assert state.business_context == "Test context"
    assert state.relevant_patterns == []
    assert state.database_schema is None
    assert state.data_dictionary == []
    assert state.sql_ddl == ""
