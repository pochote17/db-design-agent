"""LangGraph workflow compilation for the database design agent."""

from functools import partial
from pathlib import Path

from langchain_chroma import Chroma
from langgraph.graph import END, StateGraph

from .config import Settings
from .constants import MAX_ROUNDS
from .knowledge import create_vectorstore, ensure_knowledge_loaded
from .llm import create_chat_model, create_embeddings
from .models import AgentState
from .nodes import (
    check_readiness_node,
    ddl_node,
    design_node,
    dictionary_node,
    generate_questions_node,
    process_answers_node,
    retrieve_node,
)
from .security import validate_context_input


def _build_vectorstore(settings: Settings, cwd: Path) -> Chroma:
    """Build vectorstore with embeddings."""
    embeddings = create_embeddings(settings)
    chroma_dir = settings.resolve_chroma_dir(cwd)
    vectorstore = create_vectorstore(embeddings, chroma_dir)
    ensure_knowledge_loaded(vectorstore)
    return vectorstore


def _should_continue_questions(state: AgentState) -> str:
    """Determine next node after question generation."""
    if state.is_ready or state.clarification_round >= MAX_ROUNDS:
        return "design"
    return "wait_for_answers"


def _readiness_decision(state: AgentState) -> str:
    """Determine next node after readiness check."""
    if state.is_ready:
        return "design"
    return "generate_questions"


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
    workflow.add_node("generate_questions", partial(generate_questions_node, llm=llm))
    workflow.add_node("wait_for_answers", lambda state: state)  # Placeholder for human input
    workflow.add_node("process_answers", partial(process_answers_node, llm=llm))
    workflow.add_node("check_readiness", partial(check_readiness_node, llm=llm))
    workflow.add_node("design", partial(design_node, llm=llm))
    workflow.add_node("dictionary", partial(dictionary_node, llm=llm))
    workflow.add_node("ddl", partial(ddl_node, llm=llm))

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate_questions")
    workflow.add_conditional_edges(
        "generate_questions",
        _should_continue_questions,
        {
            "design": "design",
            "wait_for_answers": "wait_for_answers",
        },
    )
    workflow.add_edge("wait_for_answers", "process_answers")
    workflow.add_edge("process_answers", "check_readiness")
    workflow.add_conditional_edges(
        "check_readiness",
        _readiness_decision,
        {
            "design": "design",
            "generate_questions": "generate_questions",
        },
    )
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

    validated_context = validate_context_input(context)

    graph = build_graph(settings, cwd)
    initial_state = AgentState(business_context=validated_context, interactive=False)

    result = await graph.ainvoke(initial_state)
    return AgentState.model_validate(result)