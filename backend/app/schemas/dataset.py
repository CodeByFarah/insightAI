from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DatasetResponse(ORMModel):
    id: int
    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    uploaded_at: datetime


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    inferred_type: str
    non_null_count: int
    missing_count: int
    missing_pct: float
    unique_count: int


class DatasetPreviewResponse(BaseModel):
    dataset_id: int
    filename: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    rows: list[dict[str, str]]
    total_missing: int
    duplicate_rows: int


class DashboardResponse(BaseModel):
    dataset_count: int
    analysis_count: int
    total_rows: int
    recent_datasets: list[DatasetResponse]
    most_recent_dataset: DatasetResponse | None = None
    ai_enabled: bool = Field(
        description="Whether the AI assistant is configured on the server."
    )
