"""Dataset lifecycle: upload, listing, retrieval, deletion."""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis import build_preview
from app.core.config import get_settings
from app.core.errors import FileTooLargeError, NotFoundError
from app.models import Analysis, Dataset, User
from app.services import csv_loader, storage

logger = logging.getLogger(__name__)


def create_dataset(
    db: Session,
    user: User,
    *,
    filename: str,
    content_type: str | None,
    content: bytes,
) -> Dataset:
    """Validate, parse and persist an uploaded CSV."""
    settings = get_settings()
    if len(content) > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"The file is {len(content) // 1024} KB. The limit is "
            f"{settings.max_upload_bytes // (1024 * 1024)} MB."
        )

    safe_name = storage.validate_upload(filename, content_type)
    # Parsing before storing means an unusable file never reaches the disk.
    df = csv_loader.load_csv_bytes(content)

    storage_key = storage.build_storage_key(safe_name)
    storage.write_file(storage_key, content)

    dataset = Dataset(
        user_id=user.id,
        filename=safe_name,
        storage_key=storage_key,
        file_size_bytes=len(content),
        row_count=int(len(df)),
        column_count=int(df.shape[1]),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    logger.info("Stored dataset %s (%s rows) for user %s", dataset.id, dataset.row_count, user.id)
    return dataset


def list_datasets(db: Session, user: User, limit: int = 100) -> list[Dataset]:
    statement = (
        select(Dataset)
        .where(Dataset.user_id == user.id)
        .order_by(Dataset.uploaded_at.desc(), Dataset.id.desc())
        .limit(limit)
    )
    return list(db.execute(statement).scalars())


def get_dataset(db: Session, user: User, dataset_id: int) -> Dataset:
    """Fetch a dataset the user owns.

    A dataset belonging to someone else is reported as missing rather than
    forbidden, so the API does not confirm that the id exists.
    """
    statement = select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user.id)
    dataset = db.execute(statement).scalar_one_or_none()
    if dataset is None:
        raise NotFoundError(f"Dataset {dataset_id} was not found.")
    return dataset


def delete_dataset(db: Session, user: User, dataset_id: int) -> None:
    dataset = get_dataset(db, user, dataset_id)
    storage_key = dataset.storage_key
    db.delete(dataset)
    db.commit()
    storage.delete_file(storage_key)
    logger.info("Deleted dataset %s", dataset_id)


def load_dataframe(dataset: Dataset) -> pd.DataFrame:
    return csv_loader.load_csv_file(storage.storage_path(dataset.storage_key))


def get_preview(dataset: Dataset, row_limit: int | None = None) -> dict:
    limit = row_limit or get_settings().preview_rows
    preview = build_preview(load_dataframe(dataset), row_limit=limit)
    preview["dataset_id"] = dataset.id
    preview["filename"] = dataset.filename
    return preview


def dashboard_stats(db: Session, user: User) -> dict:
    dataset_count = db.execute(
        select(func.count(Dataset.id)).where(Dataset.user_id == user.id)
    ).scalar_one()
    analysis_count = db.execute(
        select(func.count(Analysis.id))
        .join(Dataset, Analysis.dataset_id == Dataset.id)
        .where(Dataset.user_id == user.id)
    ).scalar_one()
    total_rows = (
        db.execute(
            select(func.coalesce(func.sum(Dataset.row_count), 0)).where(Dataset.user_id == user.id)
        ).scalar_one()
        or 0
    )
    recent = list_datasets(db, user, limit=5)
    return {
        "dataset_count": int(dataset_count),
        "analysis_count": int(analysis_count),
        "total_rows": int(total_rows),
        "recent_datasets": recent,
        "most_recent_dataset": recent[0] if recent else None,
    }
