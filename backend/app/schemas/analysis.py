from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMModel


class InsightResponse(ORMModel):
    id: int
    title: str
    description: str
    category: str
    severity: str
    metric: str
    column_name: str | None = None


class VisualizationResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    x_label: str | None = None
    y_label: str | None = None
    column: str | None = None
    data: list[dict[str, Any]]
    meta: dict[str, Any] | None = None


class AnalysisResponse(BaseModel):
    id: int
    dataset_id: int
    created_at: datetime
    summary: dict[str, Any]
    insights: list[InsightResponse]
    visualizations: list[VisualizationResponse]


class AnalysisSummaryResponse(ORMModel):
    id: int
    dataset_id: int
    created_at: datetime
