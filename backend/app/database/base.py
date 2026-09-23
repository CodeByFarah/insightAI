"""Declarative base and the portable JSON column type."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, mapped_column

# JSONB on PostgreSQL (indexable, compact); plain JSON elsewhere so the test
# suite can run against SQLite without a database server.
JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_column(**kwargs):
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, **kwargs)


class Base(DeclarativeBase):
    pass
