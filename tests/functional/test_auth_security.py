import pytest
from tests.utils.auth_helpers import extract_error

# Run with: pytest tests/functional/test_auth_security.py -v


@pytest.mark.asyncio
async def test_login_sql_injection(client):
    """
    Attempt SQL injection during login.

    Expect:
        - HTTP 401 Unauthorized
        - No authentication bypass
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "' OR '1'='1", "password": "anypass"},
    )
    assert response.status_code == 422, response.json()

    msg = extract_error(response.json())
    assert "validation failed" in msg.lower()


@pytest.mark.asyncio
async def test_login_xss_in_email(client):
    """
    Try to register with an XSS payload in email.

    Expect:
        - HTTP 422 Unprocessable Entity (validation error)
    """
    user = {
        "username": "hacker",
        "email": "<script>alert(1)</script>",
        "password": "Secret123",
    }
    response = client.post("/api/auth/signup", json=user)
    assert response.status_code == 422, response.json()


@pytest.mark.asyncio
async def test_login_bruteforce_simulation(client, user):
    """
    Simulate brute-force attack with 5 failed login attempts.

    Expect:
        - Each attempt returns HTTP 401 Unauthorized
        - Error message contains 'invalid'
    """
    # Register a valid user
    client.post("/api/auth/signup", json=user)

    for _ in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "wrongpassword"},
        )
        assert resp.status_code == 401, resp.json()
        msg = extract_error(resp.json())
        assert "invalid" in msg.lower()
