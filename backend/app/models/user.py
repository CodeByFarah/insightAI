from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, timestamp_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    created_at = timestamp_column()

    datasets: Mapped[list["Dataset"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
