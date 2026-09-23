"""Conversation handling for the AI assistant.

The assistant answers from the stored analysis only: a question about a
dataset that has not been analyzed is refused rather than guessed at.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai import AIProvider, AIRequest, ChatTurn
from app.ai.context_builder import build_analysis_context, render_context
from app.ai.prompts import CONTEXT_HEADER, SYSTEM_PROMPT
from app.core.errors import AIUnavailableError
from app.models import AIConversation, AIMessage, Dataset
from app.services.analysis_service import require_latest_analysis

logger = logging.getLogger(__name__)

HISTORY_TURNS = 8


def get_or_create_conversation(db: Session, dataset: Dataset) -> AIConversation:
    statement = (
        select(AIConversation)
        .where(AIConversation.dataset_id == dataset.id)
        .options(selectinload(AIConversation.messages))
        .order_by(AIConversation.created_at.desc(), AIConversation.id.desc())
        .limit(1)
    )
    conversation = db.execute(statement).scalar_one_or_none()
    if conversation is None:
        conversation = AIConversation(dataset_id=dataset.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def get_messages(db: Session, dataset: Dataset) -> list[AIMessage]:
    return list(get_or_create_conversation(db, dataset).messages)


def ask(db: Session, dataset: Dataset, provider: AIProvider, question: str) -> AIMessage:
    """Answer a question about a dataset and persist both sides of the exchange."""
    if not provider.is_available():
        raise AIUnavailableError(
            "The AI assistant is not configured. Your dataset analysis and "
            "visualizations are still available."
        )

    analysis = require_latest_analysis(db, dataset)
    conversation = get_or_create_conversation(db, dataset)
    history = tuple(
        ChatTurn(role=message.role, content=message.content)
        for message in conversation.messages[-HISTORY_TURNS:]
    )

    context = build_analysis_context(dataset, analysis)
    request = AIRequest(
        system_prompt=SYSTEM_PROMPT,
        context=f"{CONTEXT_HEADER}{render_context(context)}",
        history=history,
        question=question,
    )

    # The user's question is recorded before the call so a failed request does
    # not silently lose what they asked.
    db.add(AIMessage(conversation_id=conversation.id, role="user", content=question))
    db.commit()

    answer_text = provider.generate(request)

    answer = AIMessage(conversation_id=conversation.id, role="assistant", content=answer_text)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    logger.info("Answered AI question for dataset %s via %s", dataset.id, provider.name)
    return answer
