import pytest
from sqlalchemy import select
from unittest.mock import AsyncMock
from jose import jwt, JWTError
from freezegun import freeze_time
from datetime import datetime, timedelta, timezone

from src.database.models import User
from src.conf.config import settings
from tests.utils.auth_helpers import extract_error


# Run with: pytest tests/functional/test_auth.py -v


# --- HELPERS ---


def expire_and_assert_invalid(token: str, client=None, path: str = None):
    """
    Simulate token expiration and assert it becomes invalid.

    - JWT decode should fail with JWTError
    - (Optional) API request must return 401

    :param token: JWT access token.
    :type token: str
    :param client: Optional FastAPI test client.
    :type client: TestClient | None
    :param path: API path to test with expired token.
    :type path: str | None
    """
    path = path or settings.TEST_PROTECTED_PATH  # usually "/api/contacts/"

    with freeze_time(
        datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_EXPIRE_MIN + 1)
    ):
        try:
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": True},
            )
            pytest.fail("Expected token to be invalid, but it was successfully decoded")
        except JWTError:
            pass

        if client is not None:
            resp = client.get(path, headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT with signature check.

    :param token: Encoded JWT.
    :type token: str
    :return: Decoded token payload.
    :rtype: dict
    :raises pytest.Fail: If decoding fails.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        pytest.fail(f"JWT decode failed: {e}")


# --- TESTS ---


@pytest.mark.asyncio
async def test_signup_success(client, user, monkeypatch):
    """User can successfully sign up and receive confirmation email."""
    monkeypatch.setattr("src.services.email.send_email", AsyncMock())

    resp = client.post("/api/auth/signup", json=user)
    assert resp.status_code == 201

    data = resp.json()
    assert "user" in data
    assert data["user"]["email"] == user["email"]
    assert "User created" in data["detail"]


@pytest.mark.asyncio
async def test_signup_duplicate(client, static_user):
    """Duplicate signup returns HTTP 409 Conflict."""
    client.post("/api/auth/signup", json=static_user)
    resp2 = client.post("/api/auth/signup", json=static_user)
    assert resp2.status_code == 409

    data = resp2.json()
    msg = extract_error(data)
    assert msg == "Account already exists"


@pytest.mark.asyncio
async def test_login_unconfirmed(client, user):
    """Login attempt fails if email not confirmed."""
    client.post("/api/auth/signup", json=user)

    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 403
    assert extract_error(resp.json()) == "Email not confirmed"


@pytest.mark.asyncio
async def test_confirm_email_and_login(client, db_session, user):
    """User can login after confirming email in DB."""
    client.post("/api/auth/signup", json=user)

    # manually confirm email in DB
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200

    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, user):
    """Login with wrong password returns 401."""
    client.post("/api/auth/signup", json=user)

    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert extract_error(resp.json()) == "Invalid password"


@pytest.mark.asyncio
async def test_login_wrong_email(client, user):
    """Login with wrong email returns 401."""
    client.post("/api/auth/signup", json=user)

    resp = client.post(
        "/api/auth/login",
        json={"email": "wrong@example.com", "password": user["password"]},
    )
    assert resp.status_code == 401
    assert extract_error(resp.json()) == "Invalid email"


@pytest.mark.asyncio
async def test_logout(client, db_session, user):
    """User can log out, refresh token is cleared, access token remains valid until expiry."""
    client.post("/api/auth/signup", json=user)

    # confirm email in DB
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    tokens = login_resp.json()
    old_access = tokens["access_token"]
    old_refresh = tokens["refresh_token"]

    # logout
    resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {old_access}"},
    )
    assert resp.status_code == 200
    assert extract_error(resp.json()) == "Successfully logged out"

    # refresh_token cleared in DB
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user = result.scalar_one()
    assert db_user.refresh_token is None

    # access token still valid immediately after logout
    payload = decode_token(old_access)
    assert payload["sub"] == user["email"]


@pytest.mark.asyncio
async def test_logout_and_relogin(client, db_session, user):
    """
    Full integration scenario:
    1. Signup + confirm email
    2. Login → first token pair
       - access works
       - simulate access expiry → access invalid
    3. Refresh token → new token pair
       - tokens differ from old ones
    4. Logout → refresh cleared in DB
       - access still valid
       - refresh invalid
       - simulate access expiry → access invalid
    5. Relogin → new token pair
       - tokens differ from previous ones
       - access works again
    """
    client.post("/api/auth/signup", json=user)

    # confirm email
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    # --- Login ---
    login_resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    old_access = tokens["access_token"]
    old_refresh = tokens["refresh_token"]

    # access works
    resp = client.get(
        "/api/contacts/", headers={"Authorization": f"Bearer {old_access}"}
    )
    assert resp.status_code in (200, 404)

    # expire access
    expire_and_assert_invalid(old_access, client)

    # --- Refresh ---
    refresh_resp = client.post(
        "/api/auth/refresh_token", json={"refresh_token": old_refresh}
    )
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    new_access = refreshed["access_token"]
    new_refresh = refreshed["refresh_token"]

    assert new_access != old_access
    assert new_refresh != old_refresh

    # --- Logout ---
    logout_resp = client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert logout_resp.status_code == 200
    assert extract_error(logout_resp.json()) == "Successfully logged out"

    # refresh cleared in DB
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user = result.scalar_one()
    assert db_user.refresh_token is None

    # access still valid
    resp_ok = client.get(
        "/api/contacts/", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert resp_ok.status_code in (200, 404)

    # refresh invalid
    bad_refresh = client.post(
        "/api/auth/refresh_token", json={"refresh_token": new_refresh}
    )
    assert bad_refresh.status_code == 401

    # expire access
    expire_and_assert_invalid(new_access, client)

    # --- Relogin ---
    relogin_resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert relogin_resp.status_code == 200
    final_tokens = relogin_resp.json()

    assert final_tokens["access_token"] != new_access
    assert final_tokens["refresh_token"] != new_refresh

    # access with new token works
    final_ok = client.get(
        "/api/contacts/",
        headers={"Authorization": f"Bearer {final_tokens['access_token']}"},
    )
    assert final_ok.status_code in (200, 404)
