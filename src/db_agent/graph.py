"""LangGraph workflow compilation for the database design agent."""

from functools import partial
from pathlib import Path

from langchain_chroma import Chroma
from langgraph.graph import END, StateGraph

from .config import Settings
from .exceptions import ConfigurationError
from .knowledge import create_vectorstore, ensure_knowledge_loaded
from .llm import create_chat_model, create_embeddings
from .models import AgentState
from .nodes import ddl_node, design_node, dictionary_node, retrieve_node


def _build_vectorstore(settings: Settings, cwd: Path) -> Chroma:
    """Build vectorstore with embeddings."""
    embeddings = create_embeddings(settings)
    chroma_dir = settings.resolve_chroma_dir(cwd)
    vectorstore = create_vectorstore(embeddings, chroma_dir)
    ensure_knowledge_loaded(vectorstore)
    return vectorstore


def build_graph(settings: Settings, cwd: Path | None = None) -> StateGraph:
    """Compile the LangGraph workflow with dependency injection."""
    if cwd is None:
        cwd = Path.cwd()

    # Create LLM
    llm = create_chat_model(settings)

    # Create vectorstore and load knowledge
    vectorstore = _build_vectorstore(settings, cwd)

    # Build graph with injected dependencies
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve", partial(retrieve_node, vectorstore=vectorstore))
    workflow.add_node("design", partial(design_node, llm=llm))
    workflow.add_node("dictionary", partial(dictionary_node, llm=llm))
    workflow.add_node("ddl", partial(ddl_node, llm=llm))

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "design")
    workflow.add_edge("design", "dictionary")
    workflow.add_edge("dictionary", "ddl")
    workflow.add_edge("ddl", END)

    return workflow.compile()


async def run_agent(
    context: str,
    settings: Settings,
    cwd: Path | None = None,
) -> AgentState:
    """Run the agent with given context and settings."""
    if cwd is None:
        cwd = Path.cwd()

    if not context or not context.strip():
        raise ConfigurationError("Business context cannot be empty")

    graph = build_graph(settings, cwd)
    initial_state = AgentState(business_context=context.strip())

    result = await graph.ainvoke(initial_state)
    return AgentState.model_validate(result)
