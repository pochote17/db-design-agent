"""Retrieve node for the database design agent."""

from langchain_chroma import Chroma

from ..knowledge import retrieve_patterns
from ..models import AgentState


def retrieve_node(state: AgentState, vectorstore: Chroma) -> dict:
    """Retrieve relevant patterns for the business context."""
    patterns = retrieve_patterns(vectorstore, state.business_context)
    return {"relevant_patterns": patterns}
