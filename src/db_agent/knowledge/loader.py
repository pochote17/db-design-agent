"""Knowledge base loader for database design patterns."""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..exceptions import KnowledgeBaseError

_PATTERNS_CONTENT = """# Database Design Patterns

## Normalization
- **1NF**: Atomic values, no repeating groups
- **2NF**: 1NF + full functional dependency on primary key
- **3NF**: 2NF + no transitive dependencies
- **BCNF**: Strict version of 3NF

## Dimensional Models (Data Warehouse)
### Star Schema
- Central fact table + denormalized dimensions
- Fast queries, controlled redundancy
- Ideal for BI/OLAP

### Snowflake Schema
- Normalized dimensions (3NF)
- Less redundancy, more joins
- Better for maintenance

## Slowly Changing Dimensions (SCD)
- **Type 0**: Keep original (no change)
- **Type 1**: Overwrite (no history)
- **Type 2**: New row with dates (full history)
- **Type 3**: Previous/current column (limited history)
- **Type 4**: Separate history table

## Domain Patterns

### E-commerce
- customers, orders, order_items, products, categories
- inventory, shipments, payments, reviews
- SCD Type 2 on customers (addresses), products (prices)

### Finance/Accounting
- chart_of_accounts, journal_entries, journal_lines
- periods, currencies, exchange_rates
- Double-entry: debit = credit always

### HR
- employees, departments, positions, salaries
- time_off, performance_reviews, benefits
- SCD Type 2 on positions, salaries, managers

### Logistics/Supply Chain
- warehouses, locations, inventory, movements
- purchase_orders, suppliers, shipments
- Full traceability (lot, serial, dates)

## Naming Conventions
- Tables: snake_case, plural (orders, order_items)
- PK: id or table_id
- FK: referenced_table_id
- Booleans: is_, has_, can_, should_
- Dates: created_at, updated_at, deleted_at
- Timestamps with timezone (timestamptz)

## Recommended Indexes
- PK automatic
- FK for frequent joins
- Columns in frequent WHERE/ORDER BY
- Composite indexes for multi-column queries
- Partial indexes (WHERE condition)

## PostgreSQL Data Types
- UUID for PK (gen_random_uuid())
- timestamptz for dates
- numeric(12,2) for money
- jsonb for flexible data
- citext for emails (case-insensitive)
- enum for fixed states"""


def get_patterns_content() -> str:
    """Get the embedded patterns content."""
    return _PATTERNS_CONTENT


def create_vectorstore(
    embeddings: Embeddings,
    persist_dir: Path,
) -> Chroma:
    """Create or load ChromaDB vectorstore."""
    persist_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
        collection_name="db_design_patterns",
    )


def ensure_knowledge_loaded(vectorstore: Chroma) -> int:
    """Load patterns into vectorstore if empty. Returns number of chunks added."""
    if vectorstore._collection.count() > 0:
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["## ", "# ", "\n\n", "\n", " ", ""],
    )

    docs = splitter.create_documents([_PATTERNS_CONTENT])
    if not docs:
        raise KnowledgeBaseError("Failed to split patterns content")

    vectorstore.add_documents(docs)
    return len(docs)


def retrieve_patterns(vectorstore: Chroma, query: str, k: int = 5) -> list[str]:
    """Retrieve relevant patterns for a query."""
    from ..security import validate_query_input
    query = validate_query_input(query)

    if not query:
        return []

    try:
        docs = vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
    except Exception as e:
        raise KnowledgeBaseError(f"Failed to retrieve patterns: {e}") from e
