from fastapi import APIRouter

from app.api.deps import AppSettings
from app.schemas.ai import AIStatusResponse

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ai/status", response_model=AIStatusResponse)
def ai_status(settings: AppSettings) -> AIStatusResponse:
    if settings.ai_enabled:
        return AIStatusResponse(
            enabled=True,
            provider="gemini",
            message="The AI assistant is ready.",
        )
    return AIStatusResponse(
        enabled=False,
        provider="none",
        message=(
            "AI analysis is currently unavailable. Your dataset analysis and "
            "visualizations are still available."
        ),
    )
