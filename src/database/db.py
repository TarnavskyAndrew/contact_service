from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
import contextlib
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings


# --- Database engine ---
#: Async SQLAlchemy engine, created using asyncpg driver.
engine = create_async_engine(settings.async_db_url, future=True, echo=True)

# --- Session factory ---
#: Factory for creating new async database sessions.
# SessionLocal = async_sessionmaker(
#     bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
# )

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


@contextlib.asynccontextmanager
async def session():
    """
    Context manager for creating a new database session.

    Handles commit/rollback automatically:

    - On success: yields a new ``AsyncSession``.
    - On exception: rolls back transaction.
    - Always: ensures session is closed.

    :yield: Active SQLAlchemy async session.
    :rtype: AsyncSession

    Example::

        async with session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
    """
    
    async with SessionLocal() as s:
        try:
            yield s
        except:
            await s.rollback()
            raise
        finally:
            await s.close()


async def get_db():
    """
    FastAPI dependency that provides a database session.

    Yields a session instance from :func:`session`, suitable for injection
    into routes and services with ``Depends``.

    :yield: Active SQLAlchemy async session.
    :rtype: AsyncSession

    Example::

        from fastapi import Depends, APIRouter
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.database.db import get_db

        router = APIRouter()

        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with session() as s:
        yield s
