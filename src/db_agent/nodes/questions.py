"""Question generation and processing nodes for interactive mode."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from ..constants import MAX_ROUNDS
from ..exceptions import ValidationError, ValidationErrorCodes
from ..models import AgentState
from ..prompts import (
    format_answer_processing_prompt,
    format_questions_prompt,
    format_readiness_prompt,
)


def generate_questions_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Generate clarifying questions for the current round."""
    if state.clarification_round >= MAX_ROUNDS:
        return {"is_ready": True}

    if state.clarification_round == 0:
        context = state.business_context
    else:
        context = state.enriched_context or state.business_context

    messages = format_questions_prompt(
        context=context,
        patterns="\n\n".join(state.relevant_patterns),
        history=state.conversation_history,
        round_number=state.clarification_round + 1,
    )

    parser = JsonOutputParser()

    try:
        chain = llm | parser
        result = chain.invoke(messages)
    except Exception as e:
        raise ValidationError(ValidationErrorCodes.SQL_PARSE_FAILED) from e

    if not isinstance(result, list):
        raise ValidationError(ValidationErrorCodes.SQL_PARSE_FAILED)

    # Validate each question
    validated_questions = []
    for _i, q in enumerate(result):
        if not isinstance(q, dict):
            continue
        required_fields = ["id", "type", "question", "reasoning"]
        if not all(field in q for field in required_fields):
            continue
        if q["type"] not in ("multiple_choice", "open_ended", "yes_no"):
            continue
        if q["type"] == "multiple_choice" and "options" not in q:
            continue
        validated_questions.append(q)

    if not validated_questions:
        raise ValidationError(ValidationErrorCodes.SQL_PARSE_FAILED)

    return {"pending_questions": validated_questions}


def process_answers_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Process user answers and generate enriched context."""
    if not state.pending_questions:
        raise ValidationError(ValidationErrorCodes.SQL_PARSE_FAILED)

    # The answers should be in the conversation_history from CLI
    # The last N entries in conversation_history are the answers
    # We need to match them with pending_questions
    answers = []
    for q in state.pending_questions:
        # Find the answer in conversation_history (last entries)
        answer_entry = next(
            (item for item in reversed(state.conversation_history)
             if item.get("question_id") == q["id"] and "answer" in item),
            None
        )
        if answer_entry:
            answers.append({
                "question_id": q["id"],
                "question": q["question"],
                "type": q["type"],
                "answer": answer_entry["answer"],
                "round": state.clarification_round + 1,
            })

    if not answers:
        raise ValidationError(ValidationErrorCodes.SQL_PARSE_FAILED)

    # Build QA pairs for the prompt
    qa_pairs = []
    for a in answers:
        qa_pairs.append({
            "question": a["question"],
            "answer": a["answer"],
            "round": a["round"],
        })

    # Determine context to enrich
    messages = format_answer_processing_prompt(
        context=state.business_context,
        qa_pairs=qa_pairs,
        patterns="\n\n".join(state.relevant_patterns),
    )

    try:
        response = llm.invoke(messages)
        enriched_context = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        raise ValidationError("Failed to generate enriched context") from e

    if not enriched_context or not enriched_context.strip():
        raise ValidationError("Empty enriched context")

    # Update conversation history with answers
    new_history = state.conversation_history.copy()
    for a in answers:
        new_history.append({
            "question_id": a["question_id"],
            "question": a["question"],
            "answer": a["answer"],
            "round": a["round"],
        })

    return {
        "enriched_context": enriched_context.strip(),
        "conversation_history": new_history,
        "clarification_round": state.clarification_round + 1,
    }


def check_readiness_node(state: AgentState, llm: BaseChatModel) -> dict:
    """Check if we have enough information to proceed to design."""
    enriched_context = state.enriched_context or state.business_context

    messages = format_readiness_prompt(
        enriched_context=enriched_context,
        patterns="\n\n".join(state.relevant_patterns),
        rounds_completed=state.clarification_round,
    )

    parser = JsonOutputParser()

    try:
        chain = llm | parser
        result = chain.invoke(messages)
    except Exception as e:
        raise ValidationError("Failed to parse readiness output") from e

    if not isinstance(result, dict):
        raise ValidationError("Readiness output must be a dict")

    is_ready = result.get("is_ready", False)
    reasoning = result.get("reasoning", "")  # Used in logging if needed

    # Force ready after max rounds
    if state.clarification_round >= MAX_ROUNDS:
        is_ready = True

    return {"is_ready": is_ready}