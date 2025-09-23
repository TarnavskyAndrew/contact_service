import pytest
from sqlalchemy import select

from src.database.models import User
from tests.utils.auth_helpers import extract_error
from src.services.auth import auth_service

# Run with: pytest tests/functional/test_login_individual.py -v


@pytest.mark.asyncio
async def test_login_success(client, make_user):
    """
    Login with valid credentials → expect 200 and tokens.
    """
    await make_user("valid@example.com", "Secret123", confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "valid@example.com", "password": "Secret123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


# @pytest.mark.asyncio
# async def test_login_invalid_password(client, make_user):
#     """
#     Login with wrong password → expect 401 Invalid password.
#     """
#     await make_user("valid@example.com", "password", confirmed=True)

#     resp = client.post(
#         "/api/auth/login", json={"email": "valid@example.com", "password": "Wrong123"}
#     )
#     assert resp.status_code == 422
#     msg = extract_error(resp.json())
#     assert msg == "Validation failed"


@pytest.mark.asyncio
async def test_login_wrong_email(client, make_user):
    """
    Login with non-existing email → expect 401 Invalid email.
    """
    await make_user("valid@example.com", "Secret123", confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "wrong@example.com", "password": "Secret123"}
    )
    assert resp.status_code == 401
    msg = extract_error(resp.json())
    assert msg == "Invalid email"


@pytest.mark.asyncio
async def test_login_unconfirmed_user(client, make_user):
    """
    Login with unconfirmed user → expect 403 Email not confirmed.
    """
    await make_user("notconfirmed@example.com", "Secret123", confirmed=False)

    resp = client.post(
        "/api/auth/login",
        json={"email": "notconfirmed@example.com", "password": "Secret123"},
    )
    assert resp.status_code == 403
    msg = extract_error(resp.json())
    assert msg == "Email not confirmed"


@pytest.mark.asyncio
async def test_login_case_sensitive_email(client, make_user):
    """
    Login should be case insensitive for email.
    """
    await make_user("case@example.com", "Secret123", confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "CASE@example.com", "password": "Secret123"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_multiple_times(client, make_user, db_session):
    """
    Login multiple times → refresh_token must be updated in DB.
    """
    await make_user("multi@example.com", "Secret123", confirmed=True)

    resp1 = client.post(
        "/api/auth/login", json={"email": "multi@example.com", "password": "Secret123"}
    )
    refresh1 = resp1.json()["refresh_token"]

    resp2 = client.post(
        "/api/auth/login", json={"email": "multi@example.com", "password": "Secret123"}
    )
    refresh2 = resp2.json()["refresh_token"]

    assert refresh1 != refresh2

    result = await db_session.execute(
        select(User).where(User.email == "multi@example.com")
    )
    db_user = result.scalar_one()
    assert db_user.refresh_token == refresh2


@pytest.mark.asyncio
async def test_login_after_logout(client, make_user):
    """
    After logout, refresh_token should be cleared.
    """
    await make_user("logout@example.com", "Secret123", confirmed=True)

    login_resp = client.post(
        "/api/auth/login", json={"email": "logout@example.com", "password": "Secret123"}
    )
    access = login_resp.json()["access_token"]

    logout_resp = client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {access}"}
    )
    assert logout_resp.status_code == 200

    # Login again works
    relogin = client.post(
        "/api/auth/login", json={"email": "logout@example.com", "password": "Secret123"}
    )
    assert relogin.status_code == 200


@pytest.mark.asyncio
async def test_login_invalid_password_after_reset(client, make_user, db_session):
    """
    After password reset, old password should not work.
    """
    user = await make_user("reset@example.com", "Secret123", confirmed=True)

    # change password in DB to a new one
    user.password = auth_service.get_password_hash("Other123")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    resp = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "Secret123"},
    )
    assert resp.status_code == 401
    msg = extract_error(resp.json())
    assert msg == "Invalid password"


@pytest.mark.asyncio
async def test_login_tokens_are_unique(client, make_user):
    """
    Access tokens should differ between subsequent logins.
    """
    await make_user("unique@example.com", "Secret123", confirmed=True)

    resp1 = client.post(
        "/api/auth/login", json={"email": "unique@example.com", "password": "Secret123"}
    )
    access1 = resp1.json()["access_token"]

    resp2 = client.post(
        "/api/auth/login", json={"email": "unique@example.com", "password": "Secret123"}
    )
    access2 = resp2.json()["access_token"]

    assert access1 != access2


@pytest.mark.asyncio
async def test_login_no_users(client):
    """
    Login when DB is empty → expect 401 Invalid email.
    """
    resp = client.post(
        "/api/auth/login", json={"email": "nouser@example.com", "password": "Secret123"}
    )
    assert resp.status_code == 401
    msg = extract_error(resp.json())
    assert msg == "Invalid email"


@pytest.mark.asyncio
async def test_login_with_special_char_password(client, make_user):
    """
    Login with a password containing special characters.
    """
    password = "P@$$w0rd!123"
    await make_user("spec@example.com", password, confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "spec@example.com", "password": password}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_with_max_length_password(client, make_user, db_session):
    """
    Login with a maximum length (64 chars) password.
    """
    long_password = "A" * 64
    await make_user("longpass@example.com", long_password, confirmed=True)

    resp = client.post(
        "/api/auth/login",
        json={"email": "longpass@example.com", "password": long_password},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    # change password in DB to a new one → old one should fail
    result = await db_session.execute(
        select(User).where(User.email == "longpass@example.com")
    )
    user = result.scalar_one()
    user.password = auth_service.get_password_hash("Other123")
    db_session.add(user)
    await db_session.commit()

    resp_fail = client.post(
        "/api/auth/login",
        json={"email": "longpass@example.com", "password": long_password},
    )
    assert resp_fail.status_code == 401
    msg = extract_error(resp_fail.json())
    assert msg == "Invalid password"


@pytest.mark.asyncio
async def test_login_password_exact_min_length(client, make_user):
    """
    Login with a password at exact minimum length (6 chars) → expect success.
    """
    password = "ABC123"
    await make_user("minpass@example.com", password, confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "minpass@example.com", "password": password}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_password_exact_max_length(client, make_user):
    """
    Login with a password at exact maximum length (64 chars) → expect success.
    """
    password = "A" * 64
    await make_user("maxpass@example.com", password, confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "maxpass@example.com", "password": password}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_signup_password_too_long(client):
    """
    Create user with password longer than max (65 chars) → expect 422.
    """
    password = "A" * 65
    resp = client.post(
        "/api/auth/signup",
        json={"email": "toolongpass@example.com", "password": password},
    )
    assert resp.status_code == 422
    msg = extract_error(resp.json())
    assert "validation failed" in msg.lower()


@pytest.mark.asyncio
async def test_login_wrong_password(client, make_user):
    """
    Login with wrong password → expect 401.
    """
    await make_user("wrongpass@example.com", "Secret123", confirmed=True)

    resp = client.post(
        "/api/auth/login",
        json={"email": "wrongpass@example.com", "password": "A" * 64},
    )
    assert resp.status_code == 401
    msg = extract_error(resp.json())
    assert "invalid password" in msg.lower()


@pytest.mark.asyncio
async def test_signup_email_max_length(client):
    """
    Create user with email at exact max length (254 chars) → expect success.
    """
    local = "a" * 64
    domain = "b" * 63 + "." + "c" * 50 + "." + "d" * 50  # 169
    email = f"{local}@{domain}.com"  # total = 234

    resp = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "Secret123", "username": "user"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "user" in data
    assert data["detail"].startswith("User created. Check your email.")


@pytest.mark.asyncio
async def test_signup_email_too_long(client):
    """
    Create user with email longer than max (255 chars) → expect 422.
    """
    domain = "b" * 185
    local = "a" * 65
    email = f"{local}@{domain}.com"  # total = 255

    resp = client.post(
        "/api/auth/signup", json={"email": email, "password": "Secret123"}
    )
    assert resp.status_code == 422
    msg = extract_error(resp.json())
    assert "validation failed" in msg.lower()


@pytest.mark.asyncio
async def test_signup_email_too_long_domain(client):
    """
    Create user with email longer than max domain (255 chars) → expect 422.
    """
    domain = "d" * 186
    local = "a" * 64
    email = f"{local}@{domain}.com"  # total = 255

    resp = client.post(
        "/api/auth/signup", json={"email": email, "password": "Secret123"}
    )
    assert resp.status_code == 422
    msg = extract_error(resp.json())
    assert "validation failed" in msg.lower()


@pytest.mark.asyncio
async def test_login_email_max_length_domain(client, make_user):
    """
    Login with email at exact max length domain (254 chars) → expect success.
    """
    domain = "d" * 185
    local = "a" * 64
    email = f"{local}@{domain}.com"  # total = 254
    await make_user(email, "Secret123", confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": email, "password": "Secret123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_password_min_length(client, make_user):
    """
    Login with password of exact min length (6 chars).
    """
    password = "ABC123"
    await make_user("min@example.com", password, confirmed=True)

    resp = client.post(
        "/api/auth/login", json={"email": "min@example.com", "password": password}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_email_too_short(client):
    """
    Email length = 5 (too short) → expect 422 validation failed.
    Example: 'a@b.c'
    """
    resp = client.post(
        "/api/auth/login",
        json={"email": "a@b.c", "password": "Secret123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_email_min_length(client, make_user):
    """
    Email length = 6 (minimum valid) → expect success if user exists.
    Example: 'a@b.co'
    """
    email = "a@b.co"  # exactly 6 characters
    password = "Secret123"
    await make_user(email, password, confirmed=True)

    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_non_existing_user(client):
    """
    Login with valid email format, but user not in DB → expect 401.
    """
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "Secret123"},
    )
    assert resp.status_code == 401
    msg = extract_error(resp.json())
    assert msg == "Invalid email"
