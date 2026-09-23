"""Schema creation.

The project creates tables from SQLAlchemy metadata rather than using a
migration tool: there is a single schema version and no production data to
migrate, so adding Alembic would be infrastructure without a purpose.
"""

import logging

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models import User  # noqa: F401  imported so metadata is populated
from app.models import Analysis, AnalysisInsight, AIConversation, AIMessage, Dataset  # noqa: F401

logger = logging.getLogger(__name__)


def create_tables(target_engine: Engine | None = None) -> None:
    Base.metadata.create_all(bind=target_engine or engine)


def ensure_default_user(db: Session) -> User:
    """Return the default user, creating it on first use."""
    email = get_settings().default_user_email
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def init_database() -> None:
    create_tables()
    with SessionLocal() as db:
        ensure_default_user(db)
    logger.info("Database schema ready")
