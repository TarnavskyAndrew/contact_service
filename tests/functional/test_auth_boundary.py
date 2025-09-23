import pytest, uuid

from tests.utils.unique_email import unique_email


# Run with: pytest tests/functional/test_auth_boundary.py -v


@pytest.mark.asyncio
async def test_password_min_length(client):
    """
    Password shorter than minimum length (6) should fail.
    """
    user = {
        "username": "mini",
        "email": unique_email("mini"),
        "password": "12345",  # length = 5
    }
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_password_exact_min_length(client):
    """
    Password with exactly minimum length (6) should succeed.
    """
    user = {
        "username": "min_ok",
        "email": unique_email("minok"),
        "password": "123456",  # length = 6
    }
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_password_max_length(client):
    """
    Password with exactly maximum length (64) should succeed.
    """
    user = {
        "username": "max_ok",
        "email": unique_email("maxok"),
        "password": "X" * 64,  # length = 64
    }
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_password_too_long(client):
    """
    Password longer than maximum length (64) should fail.
    """
    user = {
        "username": "too_long",
        "email": "toolong@example.com",
        "password": "X" * 65,  # length = 65
    }
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_username_boundary(client):
    """
    Username boundary tests:
    - Length 1 → fail
    - Length 2 → ok
    - Length 32 → ok
    - Length 33 → fail
    """
    # length = 1 → invalid
    user = {"username": "A", "email": unique_email("short"), "password": "Secret123"}
    r1 = client.post("/api/auth/signup", json=user)
    assert r1.status_code == 422

    # length = 2 → valid
    user = {"username": "AB", "email": unique_email("ok"), "password": "Secret123"}
    r2 = client.post("/api/auth/signup", json=user)
    assert r2.status_code == 201

    # length = 32 → valid
    user = {"username": "U" * 32, "email": unique_email("max"), "password": "Secret123"}
    r3 = client.post("/api/auth/signup", json=user)
    assert r3.status_code == 201

    # length = 33 → invalid
    user = {
        "username": "U" * 33,
        "email": unique_email("fail"),
        "password": "Secret123",
    }
    r4 = client.post("/api/auth/signup", json=user)
    assert r4.status_code == 422
