"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import AIProvider, get_provider
from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    db: DbSession,
    settings: AppSettings,
    x_user_email: Annotated[str | None, Header()] = None,
) -> User:
    """Identify the caller.

    Identity is a header, not a login: this project demonstrates data analysis,
    not authentication. It is still real enough to scope datasets per user, so
    the ownership checks in the services are exercised end to end.
    """
    email = (x_user_email or settings.default_user_email).strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_ai_provider() -> AIProvider:
    return get_provider()


CurrentUser = Annotated[User, Depends(get_current_user)]
Provider = Annotated[AIProvider, Depends(get_ai_provider)]
