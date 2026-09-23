"""The AI provider interface.

Everything above this layer depends on the protocol, not on Gemini. That is
what lets the tests substitute a mock provider and lets the application run
with no provider at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" or "assistant"
    content: str


@dataclass(frozen=True)
class AIRequest:
    system_prompt: str
    context: str
    history: tuple[ChatTurn, ...]
    question: str


@runtime_checkable
class AIProvider(Protocol):
    name: str

    def is_available(self) -> bool:
        """Whether the provider is configured and usable right now."""

    def generate(self, request: AIRequest) -> str:
        """Answer the question, or raise AIUnavailableError."""


class NullProvider:
    """Used when no API key is configured. The assistant is simply switched off."""

    name = "none"

    def is_available(self) -> bool:
        return False

    def generate(self, request: AIRequest) -> str:  # pragma: no cover - never called
        from app.core.errors import AIUnavailableError

        raise AIUnavailableError(
            "The AI assistant is not configured. Set GEMINI_API_KEY to enable it; "
            "your dataset analysis and visualizations are still available."
        )
