from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for response models read from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    message: str
