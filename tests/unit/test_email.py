import pytest
from unittest.mock import AsyncMock
from sqlalchemy import select

from src.database.models import User
from tests.utils.auth_helpers import extract_error


# Run with: pytest tests/unit/test_email.py -v


@pytest.mark.asyncio
async def test_resend_confirm_email_unconfirmed(client, user, monkeypatch):
    """
    Resend confirmation email for unconfirmed user.

    Expect:
        - HTTP 200
        - Message "Confirmation email resent. Check your inbox."
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    client.post("/api/auth/signup", json=user)

    resp = client.post("/api/auth/resend_confirm_email", json={"email": user["email"]})
    assert resp.status_code == 200
    msg = extract_error(resp.json())
    assert msg == "Confirmation email resent. Check your inbox."


@pytest.mark.asyncio
async def test_resend_confirm_email_already_confirmed(
    client, user, db_session, monkeypatch
):
    """
    Resend confirmation email for an already confirmed user.

    Expect:
        - HTTP 200
        - Message "User already confirmed"
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    client.post("/api/auth/signup", json=user)

    # manually confirm in DB
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    resp = client.post("/api/auth/resend_confirm_email", json={"email": user["email"]})
    assert resp.status_code == 200
    msg = extract_error(resp.json())
    assert msg == "User already confirmed"


@pytest.mark.asyncio
async def test_resend_confirm_email_nonexistent(client, monkeypatch):
    """
    Resend confirmation email for a non-existing user.

    Expect:
        - HTTP 200
        - Generic message without revealing existence
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    resp = client.post(
        "/api/auth/resend_confirm_email", json={"email": "ghost@example.com"}
    )
    assert resp.status_code == 200
    msg = extract_error(resp.json())
    assert msg == "If user exists, a confirmation email has been resent"


@pytest.mark.asyncio
async def test_request_reset_password_existing_user(client, user, monkeypatch):
    """
    Request password reset for an existing user.

    Expect:
        - HTTP 200
        - Message "Check your email for password reset link."
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    client.post("/api/auth/signup", json=user)

    resp = client.post(
        "/api/auth/request_reset_password", json={"email": user["email"]}
    )
    assert resp.status_code == 200
    msg = extract_error(resp.json())
    assert msg == "Check your email for password reset link."


@pytest.mark.asyncio
async def test_request_reset_password_nonexistent_user(client, monkeypatch):
    """
    Request password reset for a non-existing user.

    Expect:
        - HTTP 200
        - Generic message without revealing existence
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    resp = client.post(
        "/api/auth/request_reset_password", json={"email": "ghost@example.com"}
    )
    assert resp.status_code == 200
    msg = extract_error(resp.json())
    assert msg == "If user exists, an email has been sent"
