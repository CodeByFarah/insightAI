"""Optional AI layer. The rest of the application does not depend on it."""

from functools import lru_cache

from app.ai.provider import AIProvider, AIRequest, ChatTurn, NullProvider

__all__ = ["AIProvider", "AIRequest", "ChatTurn", "NullProvider", "get_provider"]


@lru_cache
def get_provider() -> AIProvider:
    """Build the configured provider, or a disabled one when no key is set."""
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.ai_enabled:
        return NullProvider()

    from app.ai.gemini_provider import GeminiProvider

    return GeminiProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
    )
