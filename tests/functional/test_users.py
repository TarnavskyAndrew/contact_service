import io
import pytest
from unittest.mock import AsyncMock
from sqlalchemy import select
from src.database.models import User
from tests.utils.auth_helpers import extract_error


# Run with: pytest tests/functional/test_users.py -v


@pytest.fixture
async def admin_headers(client, db_session):
    """
    Fixture: create an admin user, confirm email, promote to admin,
    and return Authorization header with access token.
    """
    admin_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "12345678",
    }
    # signup
    client.post("/api/auth/signup", json=admin_data)

    # confirm + promote to admin
    result = await db_session.execute(
        select(User).where(User.email == admin_data["email"])
    )
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    db_user.role = "admin"
    await db_session.commit()

    # login with JSON
    resp = client.post(
        "/api/auth/login",
        json={"email": admin_data["email"], "password": admin_data["password"]},
    )
    assert resp.status_code == 200, resp.json()
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Users API tests --- #


@pytest.mark.users
@pytest.mark.asyncio
async def test_get_users_admin(client, admin_headers):
    """
    Admin can fetch the list of all users → expect 200 and a list.
    """
    resp = client.get("/api/users/", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.users
@pytest.mark.asyncio
async def test_change_role_success(client, admin_headers, db_session, user):
    """
    Admin changes the role of an existing user → expect 200 and updated role.
    """
    # create user
    client.post("/api/auth/signup", json=user)
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    resp = client.patch(
        f"/api/users/{db_user.id}/role",
        headers=admin_headers,
        json={"role": "moderator"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "moderator"


@pytest.mark.users
@pytest.mark.asyncio
async def test_change_role_not_found(client, admin_headers):
    """
    Admin tries to change role of a non-existing user → expect 404.
    """
    resp = client.patch(
        "/api/users/999/role", headers=admin_headers, json={"role": "moderator"}
    )
    assert resp.status_code == 404
    msg = extract_error(resp.json())
    assert "user not found" in msg.lower()


@pytest.mark.users
@pytest.mark.asyncio
async def test_update_avatar_put(client, admin_headers, monkeypatch):
    """
    PUT: upload avatar via storage service mock.
    Expect: 200 and avatar_url in response.
    """

    # Patch upload_avatar where it is imported (routes.users)
    monkeypatch.setattr(
        "src.routes.users.upload_avatar",
        AsyncMock(return_value="http://fake.avatar/url"),
    )

    file_content = io.BytesIO(b"fake image data")
    resp = client.put(
        "/api/users/avatar",
        headers=admin_headers,
        files={"file": ("avatar.png", file_content, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("http://fake.avatar")


@pytest.mark.users
@pytest.mark.asyncio
async def test_update_avatar_invalid_media_type(client, admin_headers):
    """
    Uploading an invalid file type (txt instead of image) → expect 415.
    """
    file_content = io.BytesIO(b"fake text")
    resp = client.put(
        "/api/users/avatar",
        headers=admin_headers,
        files={"file": ("file.txt", file_content, "text/plain")},
    )
    assert resp.status_code == 415
    msg = extract_error(resp.json())
    assert "unsupported media type" in msg.lower()


@pytest.mark.users
@pytest.mark.asyncio
async def test_update_avatar_patch(client, admin_headers, monkeypatch):
    """
    PATCH: upload avatar directly to Cloudinary (mocked uploader).
    Expect: 200 and avatar field in response.
    """
    monkeypatch.setattr("cloudinary.uploader.upload", lambda *a, **kw: {"version": 123})
    monkeypatch.setattr(
        "cloudinary.CloudinaryImage.build_url", lambda *a, **kw: "http://fake.url"
    )

    file_content = io.BytesIO(b"fake image data")
    resp = client.patch(
        "/api/users/avatar",
        headers=admin_headers,
        files={"file": ("avatar.png", file_content, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert "avatar" in data


# --- Negative cases (non-admin) --- #


@pytest.mark.users
@pytest.mark.asyncio
async def test_get_users_forbidden_for_non_admin(client, db_session, user):
    """
    Negative: non-admin cannot fetch users list → expect 403.
    """
    # signup
    client.post("/api/auth/signup", json=user)
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    # login as normal user
    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.json()
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # forbidden
    resp2 = client.get("/api/users/", headers=headers)
    assert resp2.status_code == 403
    msg = extract_error(resp2.json())
    assert "forbidden" in msg.lower()


@pytest.mark.users
@pytest.mark.asyncio
async def test_change_role_forbidden_for_non_admin(client, db_session, user):
    """
    Negative: non-admin cannot change another user's role → expect 403.
    """
    # user A
    client.post("/api/auth/signup", json=user)
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user_a: User = result.scalar_one()
    db_user_a.confirmed = True
    await db_session.commit()

    # login as user A
    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.json()
    token_a = resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # user B
    other = {"username": "other", "email": "other@example.com", "password": "Secret123"}
    client.post("/api/auth/signup", json=other)
    result2 = await db_session.execute(select(User).where(User.email == other["email"]))
    db_user_b: User = result2.scalar_one()
    db_user_b.confirmed = True
    await db_session.commit()

    # user A tries to change role of user B
    resp_change = client.patch(
        f"/api/users/{db_user_b.id}/role", headers=headers_a, json={"role": "admin"}
    )
    assert resp_change.status_code == 403
    msg = extract_error(resp_change.json())
    assert "forbidden" in msg.lower()
