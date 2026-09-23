"""Running and retrieving analyses.

Results are persisted so repeat visits to an analysis page never recompute:
the dataset on disk is immutable, so a stored result stays correct.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analysis import analyze_dataframe
from app.core.errors import AnalysisNotFoundError
from app.models import Analysis, AnalysisInsight, Dataset
from app.services.dataset_service import load_dataframe

logger = logging.getLogger(__name__)


def get_latest_analysis(db: Session, dataset: Dataset) -> Analysis | None:
    statement = (
        select(Analysis)
        .where(Analysis.dataset_id == dataset.id)
        .options(selectinload(Analysis.insights))
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
        .limit(1)
    )
    return db.execute(statement).scalar_one_or_none()


def require_latest_analysis(db: Session, dataset: Dataset) -> Analysis:
    analysis = get_latest_analysis(db, dataset)
    if analysis is None:
        raise AnalysisNotFoundError(
            f"Dataset {dataset.id} has not been analyzed yet. Run an analysis first."
        )
    return analysis


def run_analysis(db: Session, dataset: Dataset, *, force: bool = False) -> Analysis:
    """Return the cached analysis, or compute and store a new one."""
    if not force:
        existing = get_latest_analysis(db, dataset)
        if existing is not None:
            logger.info("Reusing analysis %s for dataset %s", existing.id, dataset.id)
            return existing

    result = analyze_dataframe(load_dataframe(dataset))
    analysis = Analysis(
        dataset_id=dataset.id,
        analysis_summary=result.summary,
        visualizations=result.visualizations,
        insights=[
            AnalysisInsight(
                title=item["title"],
                description=item["description"],
                category=item["category"],
                severity=item["severity"],
                metric=item["metric"],
                column_name=item.get("column_name"),
            )
            for item in result.insights
        ],
    )
    db.add(analysis)

    # Row and column counts come from the parsed frame, which is authoritative.
    dataset.row_count = result.summary["overview"]["rows"]
    dataset.column_count = result.summary["overview"]["columns"]

    db.commit()
    db.refresh(analysis)
    logger.info("Created analysis %s for dataset %s", analysis.id, dataset.id)
    return analysis


def list_analyses(db: Session, dataset: Dataset) -> list[Analysis]:
    statement = (
        select(Analysis)
        .where(Analysis.dataset_id == dataset.id)
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
    )
    return list(db.execute(statement).scalars())
