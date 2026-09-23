"""Dataset endpoints. Routes validate and delegate; logic lives in services."""

from __future__ import annotations

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.api.deps import AppSettings, CurrentUser, DbSession
from app.core.errors import FileTooLargeError
from app.schemas.dataset import (
    DashboardResponse,
    DatasetPreviewResponse,
    DatasetResponse,
)
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])

UPLOAD_CHUNK_SIZE = 1024 * 1024


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    db: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile = File(..., description="A CSV file"),
) -> DatasetResponse:
    content = await _read_limited(file, settings.max_upload_bytes)
    dataset = dataset_service.create_dataset(
        db,
        user,
        filename=file.filename or "upload.csv",
        content_type=file.content_type,
        content=content,
    )
    return DatasetResponse.model_validate(dataset)


async def _read_limited(file: UploadFile, max_bytes: int) -> bytes:
    """Read the upload, stopping as soon as it exceeds the limit."""
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(UPLOAD_CHUNK_SIZE):
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(
                f"The file exceeds the {max_bytes // (1024 * 1024)} MB upload limit."
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[DatasetResponse]:
    datasets = dataset_service.list_datasets(db, user, limit=limit)
    return [DatasetResponse.model_validate(dataset) for dataset in datasets]


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(db: DbSession, user: CurrentUser, dataset_id: int) -> DatasetResponse:
    return DatasetResponse.model_validate(dataset_service.get_dataset(db, user, dataset_id))


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(db: DbSession, user: CurrentUser, dataset_id: int) -> Response:
    dataset_service.delete_dataset(db, user, dataset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    db: DbSession,
    user: CurrentUser,
    dataset_id: int,
    rows: int = Query(default=20, ge=1, le=100),
) -> DatasetPreviewResponse:
    dataset = dataset_service.get_dataset(db, user, dataset_id)
    return DatasetPreviewResponse.model_validate(
        dataset_service.get_preview(dataset, row_limit=rows)
    )


dashboard_router = APIRouter(tags=["dashboard"])


@dashboard_router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: DbSession, user: CurrentUser, settings: AppSettings) -> DashboardResponse:
    stats = dataset_service.dashboard_stats(db, user)
    return DashboardResponse(
        dataset_count=stats["dataset_count"],
        analysis_count=stats["analysis_count"],
        total_rows=stats["total_rows"],
        recent_datasets=[
            DatasetResponse.model_validate(item) for item in stats["recent_datasets"]
        ],
        most_recent_dataset=(
            DatasetResponse.model_validate(stats["most_recent_dataset"])
            if stats["most_recent_dataset"]
            else None
        ),
        ai_enabled=settings.ai_enabled,
    )
