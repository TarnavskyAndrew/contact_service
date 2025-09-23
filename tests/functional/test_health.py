import pytest
from sqlalchemy.exc import OperationalError
from src.database.db import get_db
from main import app
from tests.utils.auth_helpers import extract_error

# Run with: pytest tests/functional/test_health.py -v


@pytest.mark.health
def test_health_ok(client):
    """
    Health endpoint should return OK when DB is available.

    Expect:
        - HTTP 200
        - Response contains {"status": "ok", "db": "ok" or "connected"}
    """
    resp = client.get("/system/health/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] in ("ok", "connected")


@pytest.mark.health
def test_health_db_unavailable(client):
    """
    Health endpoint should return 503 when DB session raises error.

    Expect:
        - HTTP 503
        - Error message mentioning "database"
    """

    class FakeBadSession:
        async def execute(self, query):
            raise OperationalError("SELECT 1", {}, None)

    async def override_get_db():
        yield FakeBadSession()

    # Override the DB dependency
    app.dependency_overrides[get_db] = override_get_db

    resp = client.get("/system/health/")
    assert resp.status_code == 503
    msg = extract_error(resp.json())
    assert "database" in msg.lower()

    # Clear dependency overrides
    app.dependency_overrides.clear()
