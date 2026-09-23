"""Analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models import Analysis
from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisSummaryResponse,
    InsightResponse,
    VisualizationResponse,
)
from app.services import analysis_service, dataset_service

router = APIRouter(prefix="/datasets/{dataset_id}", tags=["analysis"])


def _to_response(analysis: Analysis) -> AnalysisResponse:
    return AnalysisResponse(
        id=analysis.id,
        dataset_id=analysis.dataset_id,
        created_at=analysis.created_at,
        summary=analysis.analysis_summary,
        insights=[InsightResponse.model_validate(item) for item in analysis.insights],
        visualizations=[
            VisualizationResponse.model_validate(chart) for chart in analysis.visualizations
        ],
    )


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
def run_analysis(
    db: DbSession,
    user: CurrentUser,
    dataset_id: int,
    force: bool = Query(default=False, description="Recompute even if a result is cached"),
) -> AnalysisResponse:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    return _to_response(analysis_service.run_analysis(db, dataset, force=force))


@router.get("/analysis", response_model=AnalysisResponse)
def get_analysis(db: DbSession, user: CurrentUser, dataset_id: int) -> AnalysisResponse:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    return _to_response(analysis_service.require_latest_analysis(db, dataset))


@router.get("/analyses", response_model=list[AnalysisSummaryResponse])
def list_analyses(
    db: DbSession, user: CurrentUser, dataset_id: int
) -> list[AnalysisSummaryResponse]:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    return [
        AnalysisSummaryResponse.model_validate(item)
        for item in analysis_service.list_analyses(db, dataset)
    ]


@router.get("/insights", response_model=list[InsightResponse])
def get_insights(db: DbSession, user: CurrentUser, dataset_id: int) -> list[InsightResponse]:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    analysis = analysis_service.require_latest_analysis(db, dataset)
    return [InsightResponse.model_validate(item) for item in analysis.insights]


@router.get("/visualizations", response_model=list[VisualizationResponse])
def get_visualizations(
    db: DbSession, user: CurrentUser, dataset_id: int
) -> list[VisualizationResponse]:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    analysis = analysis_service.require_latest_analysis(db, dataset)
    return [VisualizationResponse.model_validate(chart) for chart in analysis.visualizations]
