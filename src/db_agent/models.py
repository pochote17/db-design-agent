
from pydantic import BaseModel, ConfigDict, Field


class Question(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    question: str = Field(min_length=1)
    reasoning: str = ""
    options: list[str] | None = None


class Column(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    nullable: bool = False
    primary_key: bool = False
    foreign_key: str | None = None
    description: str = ""
    default: str | None = None


class Index(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    name: str = Field(min_length=1)
    columns: list[str] = Field(min_length=1)
    unique: bool = False
    where: str | None = None


class Table(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    name: str = Field(min_length=1)
    columns: list[Column] = Field(min_length=1)
    description: str = ""
    indexes: list[Index] = []


class Relationship(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    source_table: str = Field(min_length=1)
    source_column: str = Field(min_length=1)
    target_table: str = Field(min_length=1)
    target_column: str = Field(min_length=1)
    cardinality: str = Field(min_length=1, pattern=r"^(1:1|1:N|N:1|N:M)$")


class DatabaseSchema(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    tables: list[Table] = Field(min_length=1)
    relationships: list[Relationship] = []


class DataDictionaryEntry(BaseModel):
    model_config = ConfigDict(frozen=True, slots=True, extra="forbid")

    table: str = Field(min_length=1)
    column: str = Field(min_length=1)
    business_meaning: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    constraints: str = ""
    example_values: str = ""


class AgentState(BaseModel):
    model_config = ConfigDict(frozen=False, slots=True, extra="forbid")

    business_context: str = ""
    relevant_patterns: list[str] = []
    database_schema: DatabaseSchema | None = None
    data_dictionary: list[DataDictionaryEntry] = []
    sql_ddl: str = ""

    # Interactive mode fields
    conversation_history: list[dict[str, str]] = []
    pending_questions: list[Question] = []
    clarification_round: int = 0
    is_ready: bool = False
    enriched_context: str = ""
    interactive: bool = False
