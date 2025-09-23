import pytest
from sqlalchemy import select
from jose import jwt, JWTError

from src.database.models import User
from src.conf.config import settings

# Run with: pytest tests/functional/test_tokens.py -v

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_EXPIRE_MIN * 60
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_EXPIRE_DAYS * 24 * 60 * 60


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


@pytest.mark.asyncio
async def test_access_token_lifetime(client, db_session, user):
    """
    Test that access_token has valid structure and correct lifetime
    according to settings.ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    # signup and confirm user
    client.post("/api/auth/signup", json=user)
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    # login with JSON
    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.json()
    tokens = resp.json()
    payload = decode_token(tokens["access_token"])

    # Universal checks
    assert payload["sub"] == user["email"]
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]

    # Lifetime check
    lifetime = payload["exp"] - payload["iat"]
    expected = ACCESS_TOKEN_EXPIRE_MINUTES
    assert lifetime == expected


@pytest.mark.asyncio
async def test_refresh_token_lifetime(client, db_session, user):
    """
    Test that refresh_token has valid structure and correct lifetime
    according to settings.REFRESH_TOKEN_EXPIRE_DAYS.
    """
    client.post("/api/auth/signup", json=user)
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    # login with JSON
    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.json()
    tokens = resp.json()
    payload = decode_token(tokens["refresh_token"])

    # Universal checks
    assert payload["sub"] == user["email"]
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]

    # Lifetime check
    lifetime = payload["exp"] - payload["iat"]
    expected = REFRESH_TOKEN_EXPIRE_DAYS
    assert lifetime == expected
