import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.middleware import setup_middlewares


# Run with: pytest tests/unit/test_middleware.py -v

def create_app():
    """
    Helper: create a temporary FastAPI app with middleware enabled.
    """
    app = FastAPI()
    setup_middlewares(app)

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    return app


def test_process_time_header():
    """
    Middleware should add X-Process-Time header to responses.

    → expect 200 and header value convertible to float ≥ 0
    """
    app = create_app()
    client = TestClient(app)

    response = client.get("/ping")
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) >= 0


def test_cors_headers():
    """
    Middleware should add CORS headers for OPTIONS preflight request.

    → expect 200 and valid CORS headers
    """
    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/ping",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200

    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin in ("*", "http://localhost:3000")
    assert "access-control-allow-methods" in response.headers
