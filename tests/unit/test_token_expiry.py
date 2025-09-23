import pytest
from freezegun import freeze_time
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from src.services.auth import auth_service
from src.conf.config import settings


# Run with: pytest tests/unit/test_token_expiry.py -v

EMAIL = "test@example.com"


def decode(token: str):
    """
    Decode JWT using project settings.

    :param token: Encoded JWT
    :type token: str
    :return: Decoded JWT payload
    :rtype: dict
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


@pytest.mark.asyncio
async def test_access_token_lifetime():
    """
    Access token should have a lifetime equal to settings.ACCESS_EXPIRE_MIN.
    """
    token = await auth_service.create_access_token(data={"sub": EMAIL})
    payload = decode(token)

    assert payload["sub"] == EMAIL
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)

    lifetime = payload["exp"] - payload["iat"]
    assert lifetime == settings.ACCESS_EXPIRE_MIN * 60


@pytest.mark.asyncio
async def test_access_token_expiry_with_time_freeze():
    """
    Access token should be valid before expiry and invalid after expiry.
    """
    token = await auth_service.create_access_token(data={"sub": EMAIL})

    # Before expiry
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_EXPIRE_MIN - 1)
    ):
        payload = decode(token)
        assert payload["sub"] == EMAIL

    # After expiry
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_EXPIRE_MIN + 1)
    ):
        with pytest.raises(JWTError):
            decode(token)


@pytest.mark.asyncio
async def test_refresh_token_lifetime():
    """
    Refresh token should have a lifetime equal to settings.REFRESH_EXPIRE_DAYS.
    """
    token = await auth_service.create_refresh_token(data={"sub": EMAIL})
    payload = decode(token)

    lifetime = payload["exp"] - payload["iat"]
    assert lifetime == settings.REFRESH_EXPIRE_DAYS * 24 * 60 * 60


@pytest.mark.asyncio
async def test_refresh_token_expiry_with_time_freeze():
    """
    Refresh token should be valid before expiry and invalid after expiry.
    """
    token = await auth_service.create_refresh_token(data={"sub": EMAIL})

    # Before expiry
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_EXPIRE_DAYS - 1)
    ):
        payload = decode(token)
        assert payload["sub"] == EMAIL

    # After expiry
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_EXPIRE_DAYS + 1)
    ):
        with pytest.raises(JWTError):
            decode(token)


@pytest.mark.asyncio
async def test_access_token_can_be_reissued_after_expiry():
    """
    After an access token expires, new access and refresh tokens can be issued.
    """
    # Issue initial access token
    token = await auth_service.create_access_token(data={"sub": EMAIL})

    # Move time forward beyond expiry
    with freeze_time(
        datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_EXPIRE_MIN + 1)
    ):
        # Old token should be invalid
        with pytest.raises(JWTError):
            decode(token)

        # Issue new tokens
        new_access = await auth_service.create_access_token(data={"sub": EMAIL})
        new_refresh = await auth_service.create_refresh_token(data={"sub": EMAIL})

        payload_access = decode(new_access)
        payload_refresh = decode(new_refresh)

        # Verify new tokens are valid
        assert payload_access["sub"] == EMAIL
        assert payload_refresh["sub"] == EMAIL
        assert payload_access["exp"] > payload_access["iat"]
        assert payload_refresh["exp"] > payload_refresh["iat"]
