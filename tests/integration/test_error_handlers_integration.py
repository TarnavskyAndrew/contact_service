import pytest
from fastapi import status
from sqlalchemy.exc import OperationalError
from src.database.db import get_db


# Run with: pytest tests/integration/test_error_handlers_integration.py -v

# ----------------------------------------------------------------------
# Integration tests: real HTTP calls
# ----------------------------------------------------------------------


def test_http_exception_integration(client):
    """
    Integration: non-existent route should trigger HTTPException handler (404).
    """
    resp = client.get("/nonexistent-url")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == 404
    assert body["error"]["message"] in ("Not Found", "Not found")


def test_validation_error_integration(client):
    """
    Integration: invalid signup payload should trigger validation handler (422).
    """
    resp = client.post("/api/auth/signup", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == 422
    assert body["error"]["message"] == "Validation failed"
    assert "details" in body["error"]


def test_integrity_error_integration(client, user):
    """
    Integration: duplicate user registration should trigger IntegrityError handler (409/400).
    """
    resp1 = client.post("/api/auth/signup", json=user)
    assert resp1.status_code in (200, 201)

    resp2 = client.post("/api/auth/signup", json=user)
    assert resp2.status_code in (400, 409)
    body = resp2.json()
    assert body["error"]["code"] in (400, 409)


def test_sqlalchemy_error_integration(client):
    """
    Integration: simulate broken DB connection to trigger SQLAlchemyError handler (500).
    """

    async def broken_get_db():
        raise OperationalError("SELECT 1", {}, Exception("DB down"))

    client.app.dependency_overrides[get_db] = broken_get_db

    resp = client.get("/system/health/")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == 500
    assert body["error"]["message"] == "Database error"
