import pytest
from unittest.mock import AsyncMock

# Run with: pytest tests/functional/test_debug.py -v


@pytest.mark.debug
@pytest.mark.asyncio
async def test_debug_send(client, monkeypatch):
    """
    Test the debug endpoint `/api/debug/send`.

    Expect:
        - Mocked email sending is called
        - Response returns {"ok": True}
    """
    monkeypatch.setattr("src.services.email.send_email", AsyncMock(return_value=True))

    resp = client.post("/api/debug/send", json={"email": "test@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


@pytest.mark.debug
def test_debug_routes(client):
    """
    Test the debug endpoint `/api/debug/__routes`.

    Expect:
        - Response contains a list of routes
        - `/api/auth/signup` route is present
        - Valid CORS headers are returned
    """
    resp = client.get(
        "/api/debug/__routes", headers={"Origin": "http://localhost:3000"}
    )
    assert resp.status_code == 200
    data = resp.json()

    # basic structure
    assert "routes" in data
    assert isinstance(data["routes"], list)

    # ensure auth route is present
    paths = [r["path"] for r in data["routes"]]
    assert "/api/auth/signup" in paths

    # CORS header check
    assert resp.headers["access-control-allow-origin"] in ["*", "http://localhost:3000"]
