"""Knowledge base module for db-design-agent."""

from .loader import (
    create_vectorstore,
    ensure_knowledge_loaded,
    get_patterns_content,
    retrieve_patterns,
)

__all__ = [
    "create_vectorstore",
    "ensure_knowledge_loaded",
    "get_patterns_content",
    "retrieve_patterns",
]
