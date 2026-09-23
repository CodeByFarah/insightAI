from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

MAX_QUESTION_LENGTH = 1000


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=MAX_QUESTION_LENGTH)

    @field_validator("question")
    @classmethod
    def _strip(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Ask a question of at least 3 characters.")
        return cleaned


class ChatMessage(ORMModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    dataset_id: int
    answer: ChatMessage


class ConversationResponse(BaseModel):
    dataset_id: int
    ai_enabled: bool
    messages: list[ChatMessage]


class AIStatusResponse(BaseModel):
    enabled: bool
    provider: str
    message: str
