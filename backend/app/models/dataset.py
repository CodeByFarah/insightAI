from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, timestamp_column


class Dataset(Base):
    """Metadata about an uploaded CSV. The rows themselves live on disk."""

    __tablename__ = "datasets"
    __table_args__ = (
        CheckConstraint("row_count >= 0", name="ck_datasets_row_count_non_negative"),
        CheckConstraint("column_count >= 0", name="ck_datasets_column_count_non_negative"),
        Index("ix_datasets_user_uploaded_at", "user_id", "uploaded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    row_count: Mapped[int] = mapped_column(nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(nullable=False, default=0)
    uploaded_at = timestamp_column(index=True)

    user: Mapped["User"] = relationship(back_populates="datasets")  # noqa: F821
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="Analysis.created_at.desc()",
    )
    conversations: Mapped[list["AIConversation"]] = relationship(  # noqa: F821
        back_populates="dataset", cascade="all, delete-orphan"
    )
