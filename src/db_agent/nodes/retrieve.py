"""Retrieve node for the database design agent."""

from langchain_chroma import Chroma

from ..knowledge import retrieve_patterns
from ..models import AgentState
from ..security import validate_query_input


def retrieve_node(state: AgentState, vectorstore: Chroma) -> dict:
    """Retrieve relevant patterns for the business context."""
    query = validate_query_input(state.business_context)
    patterns = retrieve_patterns(vectorstore, query)
    return {"relevant_patterns": patterns}