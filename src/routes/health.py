from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db


router = APIRouter(prefix="/health", tags=["System"])


@router.get("/", summary="Healthcheck")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Healthcheck endpoint for system readiness.

    - Executes a simple ``SELECT 1`` query against the database.
    - If the query fails or returns no result → service is considered unavailable.

    :param db: Active database session (dependency).
    :type db: AsyncSession
    :raises HTTPException: 503 if database is unavailable.
    :return: JSON with service and database status.
    :rtype: dict

    Example response (healthy)::

        {
            "status": "ok",
            "db": "connected"
        }

    Example response (unhealthy)::

        {
            "detail": "Database not available"
        }
    """

    try:
        result = (await db.execute(text("SELECT 1"))).scalar()
        if result != 1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )
        return {"status": "ok", "db": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )
