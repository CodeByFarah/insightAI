"""A deterministic provider used by the test suite.

Tests must never depend on a live Gemini request, so the behaviour under test
is the application's handling of a provider, not the model itself.
"""

from __future__ import annotations

from collections.abc import Callable

from app.ai.provider import AIRequest
from app.core.errors import AIUnavailableError


class MockAIProvider:
    """Returns a canned answer, or raises whatever failure a test asks for."""

    name = "mock"

    def __init__(
        self,
        response: str = "Based on the provided analysis, the dataset looks complete.",
        *,
        available: bool = True,
        error: Exception | None = None,
        handler: Callable[[AIRequest], str] | None = None,
    ):
        self._response = response
        self._available = available
        self._error = error
        self._handler = handler
        self.requests: list[AIRequest] = []

    def is_available(self) -> bool:
        return self._available

    def generate(self, request: AIRequest) -> str:
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        if self._handler is not None:
            return self._handler(request)
        if not self._response.strip():
            raise AIUnavailableError(
                "The AI assistant returned an empty response. Please try again."
            )
        return self._response
