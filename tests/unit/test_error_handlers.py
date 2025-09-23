import pytest
import json
from starlette.requests import Request
from fastapi import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core import error_handlers

# Run with: pytest tests/unit/test_error_handlers.py -v


def make_request(path="/test", method="POST"):
    """
    Helper to create a fake Starlette Request.

    :param path: Request path.
    :type path: str
    :param method: HTTP method.
    :type method: str
    :return: Fake Starlette Request object.
    :rtype: Request
    """
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validation_error_handler_with_dict():
    """
    Validation error handler should process standard Pydantic-style dict errors.

    → expect 422, details list with field info.
    """
    request = make_request("/signup")

    class FakeValidationError(Exception):
        def errors(self):
            return [
                {
                    "loc": ["body", "email"],
                    "msg": "field required",
                    "type": "value_error",
                }
            ]

    exc = FakeValidationError()

    resp = await error_handlers.validation_exception_handler(request, exc)
    body = json.loads(resp.body.decode())

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    details = body["error"]["details"]
    assert isinstance(details, list)
    assert details[0]["msg"] == "field required"
    assert details[0]["type"] == "value_error"
    assert details[0]["loc"] == ["body", "email"]


@pytest.mark.asyncio
async def test_validation_error_handler_with_valueerror():
    """
    Validation error handler should normalize ValueError.

    → expect 422, details with msg, type=value_error, loc=[]
    """
    request = make_request("/signup")

    class FakeValidationError(Exception):
        def errors(self):
            return [ValueError("Invalid email format")]

    exc = FakeValidationError()

    resp = await error_handlers.validation_exception_handler(request, exc)
    body = json.loads(resp.body.decode())

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    details = body["error"]["details"]
    assert isinstance(details, list)
    assert details[0]["msg"] == "Invalid email format"
    assert details[0]["type"] == "value_error"
    assert details[0]["loc"] == []


@pytest.mark.asyncio
async def test_http_exception_handler():
    """
    HTTP exception handler should return the error response.

    → expect 404 with message "Not found"
    """
    request = make_request("/not-found", method="GET")
    exc = StarletteHTTPException(status_code=404, detail="Not found")

    resp = await error_handlers.http_exception_handler(request, exc)
    body = json.loads(resp.body.decode())

    assert resp.status_code == 404
    assert body["error"]["message"] == "Not found"


@pytest.mark.asyncio
async def test_integrity_error_handler():
    """
    IntegrityError handler should map DB duplicate errors.

    → expect 400 or 409
    """
    request = make_request("/signup")
    exc = IntegrityError("stmt", {}, Exception("duplicate key"))

    resp = await error_handlers.integrity_error_handler(request, exc)
    body = json.loads(resp.body.decode())

    assert resp.status_code in (400, 409)
    assert body["error"]["code"] in (400, 409)


@pytest.mark.asyncio
async def test_sqlalchemy_error_handler():
    """
    SQLAlchemyError handler should catch generic DB errors.

    → expect 500 with "Database error"
    """
    request = make_request("/contacts", method="GET")
    exc = SQLAlchemyError("db broken")

    resp = await error_handlers.sqlalchemy_error_handler(request, exc)
    body = json.loads(resp.body.decode())

    assert resp.status_code == 500
    assert body["error"]["message"] == "Database error"


@pytest.mark.asyncio
async def test_generic_exception_handler():
    """
    Generic exception handler should catch unhandled errors.

    → expect 500 with "Internal server error"
    """
    request = make_request("/force-exception", method="GET")
    exc = Exception("unexpected")

    resp = await error_handlers.on_unhandled(request, exc)
    body = json.loads(resp.body.decode())

    assert resp.status_code == 500
    assert body["error"]["message"] == "Internal server error"
