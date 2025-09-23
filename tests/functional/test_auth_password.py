import pytest
from unittest.mock import AsyncMock
from sqlalchemy import select
from jose import jwt

from src.database.models import User
from src.conf.config import settings
from src.services.auth import auth_service
from tests.utils.auth_helpers import extract_error

# Run with: pytest tests/functional/test_auth_password.py -v


@pytest.mark.asyncio
async def test_resend_confirm_email(client, user, monkeypatch):
    """
    Resend confirmation email:

    - Non-existing (ghost) user → still returns "resent" message.
    - Existing unconfirmed user → returns resent confirmation message.
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    # ghost user
    resp = client.post(
        "/api/auth/resend_confirm_email", json={"email": "ghost@example.com"}
    )
    assert resp.status_code == 200
    assert "resent" in resp.json()["message"].lower()

    # unconfirmed user
    resp = client.post("/api/auth/resend_confirm_email", json={"email": user["email"]})
    assert resp.status_code == 200
    assert (
        "resent" in resp.json()["message"].lower()
        or "already confirmed" in resp.json()["message"].lower()
    )


@pytest.mark.asyncio
async def test_refresh_token_success(client, db_session, user, monkeypatch):
    """
    Refresh token flow:
    - Login to get tokens
    - Call refresh endpoint
    - New tokens are issued and differ from the old ones
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    # signup
    client.post("/api/auth/signup", json=user)

    # confirm manually in DB
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    # login
    login_resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert login_resp.status_code == 200, login_resp.json()
    tokens = login_resp.json()
    old_refresh = tokens["refresh_token"]

    # refresh
    resp = client.post("/api/auth/refresh_token", json={"refresh_token": old_refresh})
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != old_refresh


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """
    Refresh with invalid token → should fail with 401 Unauthorized.
    """
    resp = client.post(
        "/api/auth/refresh_token", json={"refresh_token": "invalid.token"}
    )
    assert resp.status_code == 401

    msg = extract_error(resp.json())
    assert "invalid" in msg.lower()


@pytest.mark.asyncio
async def test_request_reset_password_and_reset(client, db_session, user, monkeypatch):
    """
    End-to-end password reset flow:
    - Request reset → confirmation message
    - Generate reset token manually
    - Call reset endpoint with new password
    - Verify that the password is updated in DB
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    # signup
    client.post("/api/auth/signup", json=user)

    # request reset
    resp = client.post(
        "/api/auth/request_reset_password", json={"email": user["email"]}
    )
    assert resp.status_code == 200
    msg = extract_error(resp.json())
    assert "reset" in msg.lower()

    # fetch user
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()

    # create reset token
    reset_token = jwt.encode(
        {"sub": db_user.email, "scope": "reset_password"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    # reset password
    resp2 = client.post(
        f"/api/auth/reset_password/{reset_token}", json={"new_password": "newpwd123"}
    )
    assert resp2.status_code == 200
    msg2 = extract_error(resp2.json())
    assert "success" in msg2.lower()

    # clear session cache to ensure fresh DB state
    db_session.expire_all()

    # re-fetch user and verify new password
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    updated_user: User = result.scalar_one()

    assert auth_service.verify_password("newpwd123", updated_user.password)
