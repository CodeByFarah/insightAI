"""Test configuration.

The suite runs against SQLite and a temporary storage directory, so no
PostgreSQL server and no network access are required.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP_ROOT = Path(tempfile.mkdtemp(prefix="insightai-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(_TMP_ROOT / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = str(_TMP_ROOT / "storage")
os.environ["GEMINI_API_KEY"] = ""
os.environ["DEFAULT_USER_EMAIL"] = "tester@insightai.local"
os.environ["MAX_UPLOAD_BYTES"] = str(1024 * 1024)  # 1 MB keeps the limit test fast

from fastapi.testclient import TestClient  # noqa: E402

from app.ai.mock_provider import MockAIProvider  # noqa: E402
from app.api.deps import get_ai_provider  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

SAMPLE_CSV = (
    "customer_id,age,monthly_spend,plan,signup_date\n"
    "C1,34,49.5,basic,2024-01-05\n"
    "C2,,71.0,premium,2024-01-09\n"
    "C3,45,88.25,premium,2024-02-01\n"
    "C4,29,31.75,basic,2024-02-14\n"
    "C5,52,120.0,premium,2024-03-02\n"
    "C6,41,64.4,basic,2024-03-19\n"
)


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    # raise_server_exceptions=False exercises the production 500 handler.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def mock_provider():
    """Install a mock AI provider and hand it to the test."""
    provider = MockAIProvider()
    app.dependency_overrides[get_ai_provider] = lambda: provider
    yield provider
    app.dependency_overrides.pop(get_ai_provider, None)


@pytest.fixture
def use_provider():
    """Install a caller-supplied provider for one test."""
    installed = []

    def _install(provider):
        app.dependency_overrides[get_ai_provider] = lambda: provider
        installed.append(provider)
        return provider

    yield _install
    app.dependency_overrides.pop(get_ai_provider, None)


@pytest.fixture
def uploaded_dataset(client):
    response = client.post(
        "/api/datasets",
        files={"file": ("customers.csv", SAMPLE_CSV, "text/csv")},
    )
    assert response.status_code == 201, response.text
    return response.json()
