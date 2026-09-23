"""AI assistant endpoints. Optional by design."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AppSettings, CurrentUser, DbSession, Provider
from app.schemas.ai import ChatMessage, ChatRequest, ChatResponse, ConversationResponse
from app.services import ai_service, dataset_service

router = APIRouter(prefix="/datasets/{dataset_id}/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    db: DbSession,
    user: CurrentUser,
    provider: Provider,
    dataset_id: int,
    payload: ChatRequest,
) -> ChatResponse:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    answer = ai_service.ask(db, dataset, provider, payload.question)
    return ChatResponse(dataset_id=dataset_id, answer=ChatMessage.model_validate(answer))


@router.get("/messages", response_model=ConversationResponse)
def conversation(
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    dataset_id: int,
) -> ConversationResponse:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    return ConversationResponse(
        dataset_id=dataset_id,
        ai_enabled=settings.ai_enabled,
        messages=[ChatMessage.model_validate(item) for item in ai_service.get_messages(db, dataset)],
    )
