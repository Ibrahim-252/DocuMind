import os
import tempfile

# Test settings must be in place BEFORE the app is imported.
os.environ.setdefault("EMBEDDING_BACKEND", "fake")
os.environ.setdefault("SIMILARITY_THRESHOLD", "0.05")
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="documind-uploads-"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _schema():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def client(_schema):
    """A test client on an empty database. Background tasks run before the response returns."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE chunks, documents RESTART IDENTITY CASCADE"))
    with TestClient(app) as test_client:
        yield test_client


def upload_text(client: TestClient, filename: str, content: str):
    return client.post("/documents", files={"file": (filename, content.encode(), "text/plain")})
