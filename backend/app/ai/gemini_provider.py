"""Gemini-backed implementation of the AI provider protocol."""

from __future__ import annotations

import logging

from app.ai.provider import AIRequest
from app.core.errors import AIUnavailableError

logger = logging.getLogger(__name__)

TIMEOUT_HINTS = ("timeout", "deadline", "timed out")
RATE_LIMIT_HINTS = ("rate limit", "quota", "429", "resource_exhausted")
AUTH_HINTS = ("api key", "unauthenticated", "permission denied", "401", "403")


class GeminiProvider:
    """Calls the Gemini API through the official google-genai SDK.

    Every failure is translated into AIUnavailableError with a message that is
    safe to show a user: the underlying exception is logged, never returned.
    """

    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 30.0):
        self._api_key = api_key
        self._model = model
        self._timeout_ms = int(timeout_seconds * 1000)
        self._client = None

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depends on the environment
            logger.error("google-genai is not installed: %s", exc)
            raise AIUnavailableError() from exc
        self._client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=self._timeout_ms),
        )
        return self._client

    def generate(self, request: AIRequest) -> str:
        if not self.is_available():
            raise AIUnavailableError(
                "The AI assistant is not configured. Set GEMINI_API_KEY to enable it."
            )
        client = self._get_client()
        from google.genai import types

        contents = [
            types.Content(
                role="user" if turn.role == "user" else "model",
                parts=[types.Part(text=turn.content)],
            )
            for turn in request.history
        ]
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=f"{request.context}\n\nQuestion: {request.question}")],
            )
        )

        try:
            response = client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=request.system_prompt,
                    temperature=0.2,
                    max_output_tokens=800,
                ),
            )
        except Exception as exc:  # the SDK raises a wide range of transport errors
            raise self._translate(exc) from exc

        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: object) -> str:
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            logger.warning("Gemini returned a response with no usable text")
            raise AIUnavailableError(
                "The AI assistant returned an empty response. Please try asking again."
            )
        return text

    @staticmethod
    def _translate(exc: Exception) -> AIUnavailableError:
        message = str(exc).lower()
        logger.warning("Gemini request failed: %s", type(exc).__name__, exc_info=exc)
        if any(hint in message for hint in TIMEOUT_HINTS):
            return AIUnavailableError(
                "The AI assistant did not respond in time. Your analysis and "
                "visualizations are still available."
            )
        if any(hint in message for hint in RATE_LIMIT_HINTS):
            return AIUnavailableError(
                "The AI assistant has hit its request limit. Please try again shortly."
            )
        if any(hint in message for hint in AUTH_HINTS):
            return AIUnavailableError(
                "The AI assistant is not configured correctly. Check the server "
                "configuration; your analysis is still available."
            )
        return AIUnavailableError()
