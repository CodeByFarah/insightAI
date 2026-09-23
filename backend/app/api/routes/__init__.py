from fastapi import APIRouter

from app.api.routes import ai, analyses, datasets, health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(datasets.router)
api_router.include_router(datasets.dashboard_router)
api_router.include_router(analyses.router)
api_router.include_router(ai.router)

__all__ = ["api_router"]
