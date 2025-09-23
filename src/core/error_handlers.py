from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

try:
    from psycopg2.errors import UniqueViolation
except Exception:
    UniqueViolation = None  # type: ignore


def _error_payload(
    code: int,
    message: str,
    request: Request,
    *,
    details: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build a unified error response payload.

    :param code: HTTP status code
    :param message: Short description of the error
    :param request: FastAPI Request instance
    :param details: Optional validation or debug details
    :return: Dict with structured error information
    """
    payload: Dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    if details:
        payload["error"]["details"] = details
    return payload


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors (HTTP 422).

    Converts Pydantic's error format into a JSON-safe response.
    Ensures raw Python exceptions (e.g. ValueError) are converted
    into serializable dictionaries.

    Example response::

        {
            "error": {
                "code": 422,
                "message": "Validation failed",
                "path": "/api/auth/signup",
                "method": "POST",
                "timestamp": "2025-09-18T12:34:56Z",
                "details": [
                    {"loc": ["body", "email"], "msg": "Invalid email format", "type": "value_error"}
                ]
            }
        }
    """
    details: List[Dict[str, Any]] = []

    for err in exc.errors():
        if isinstance(err, dict):
            details.append(
                {
                    "loc": err.get("loc", []),
                    "msg": err.get("msg", ""),
                    "type": err.get("type", ""),
                }
            )
        else:
            # Convert raw exceptions like ValueError
            details.append({"loc": [], "msg": str(err), "type": "value_error"})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(422, "Validation failed", request, details=details),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle generic HTTP exceptions (400–404, 401, etc.).
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            exc.status_code, str(exc.detail or "HTTP error"), request
        ),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Handle database integrity errors.

    - 409 Conflict → unique constraint violation
    - 400 Bad Request → other integrity issues
    """
    is_unique = bool(
        UniqueViolation and isinstance(getattr(exc, "orig", None), UniqueViolation)
    )
    code = status.HTTP_409_CONFLICT if is_unique else status.HTTP_400_BAD_REQUEST
    msg = (
        "Duplicate value violates unique constraint"
        if is_unique
        else "Database integrity error"
    )
    return JSONResponse(status_code=code, content=_error_payload(code, msg, request))


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle generic SQLAlchemy errors (HTTP 500).
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(500, "Database error", request),
    )


async def on_unhandled(request: Request, exc: Exception):
    """
    Handle any unhandled exceptions (HTTP 500).
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(500, "Internal server error", request),
    )


def init_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the FastAPI app.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, on_unhandled)
