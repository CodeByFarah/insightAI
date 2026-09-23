from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, JSONType, timestamp_column


class Analysis(Base):
    """A completed analysis run. The full computed result is cached as JSON."""

    __tablename__ = "analyses"
    __table_args__ = (Index("ix_analyses_dataset_created_at", "dataset_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_summary: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    visualizations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONType, nullable=False, default=list
    )
    created_at = timestamp_column(index=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="analyses")  # noqa: F821
    insights: Mapped[list["AnalysisInsight"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", order_by="AnalysisInsight.id"
    )


class AnalysisInsight(Base):
    """One finding derived from the computed statistics."""

    __tablename__ = "analysis_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    metric: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    column_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at = timestamp_column()

    analysis: Mapped["Analysis"] = relationship(back_populates="insights")
