import pytest, uuid
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import APIRouter
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter import FastAPILimiter

from httpx import AsyncClient, ASGITransport


from src.database.models import Base, User
from src.repository import users
from src.schemas import UserModel
from main import app
from src.database.db import get_db, SessionLocal
from src.services.auth import auth_service
from src.repository import users as repo


# Async SQLite для тестов
SQLALCHEMY_TEST_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(SQLALCHEMY_TEST_URL, echo=False, future=True)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# --- DB Session ---
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Create a clean test DB before each test and return an AsyncSession.

    :return: Database session for the test.
    :rtype: AsyncSession
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session


# --- Contackt fixtures ---
@pytest.fixture
def contact_payload():
    """
    Basic contact payload template.
    Can be copied and modified in tests for unique email/phone.

    :return: Contact data dictionary.
    :rtype: dict
    """
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "123456789",
        "birthday": "1990-01-01",
        "extra": "friend",
    }


# --- User fixtures ---
@pytest.fixture
def test_user_data():
    """
    Fixed user data for repository unit tests.

    :return: User Pydantic model.
    :rtype: UserModel
    """
    return UserModel(
        username="testuser",
        email="test@example.com",
        password="secret123",
    )


@pytest.fixture
def user():
    """
    Generate a unique user dict (for API requests).

    :return: User data dictionary.
    :rtype: dict
    """
    return {
        "username": f"user_{uuid.uuid4().hex[:6]}",
        "email": f"{uuid.uuid4().hex[:6]}@example.com",
        "password": "Secret123",
    }


@pytest.fixture
def static_user():
    """
    Static user with fixed email (for duplicate tests).

    :return: User data dictionary.
    :rtype: dict
    """
    return {
        "username": "duplicate_user",
        "email": "dup@example.com",
        "password": "Secret123",
    }


@pytest_asyncio.fixture
async def create_user_in_db(db_session, test_user_data):
    """
    Create a real user in the DB using the repository.

    :param db_session: Database session.
    :type db_session: AsyncSession
    :param test_user_data: User data model.
    :type test_user_data: UserModel
    :return: Created User instance.
    :rtype: User
    """
    password_hash = "hashed_pwd"
    user = await users.create_user(test_user_data, password_hash, db_session)
    return user


@pytest.fixture
async def make_user(db_session):
    """
    Factory fixture to create a user in the DB.

    Usage:
        user = await make_user("test@example.com", "Secret123", confirmed=True/False)

    :param db_session: Database session.
    :type db_session: AsyncSession
    :return: Factory function to create users.
    :rtype: Callable
    """

    async def _make(
        email: str,
        password: str,
        confirmed: bool = True,
        username: str | None = "testuser",  # optional
    ) -> User:
        body = UserModel(username=username, email=email, password=password)

        user = await repo.create_user(
            body=body,
            password_hash=auth_service.get_password_hash(password),
            db=db_session,
        )

        # Explicitly set confirmed and save
        user.confirmed = confirmed
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return user

    return _make


# --- FastAPI client ---
@pytest.fixture(scope="function")
def client():
    """
    TestClient with overridden get_db (async).

    :return: TestClient instance.
    :rtype: TestClient
    """

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# --- Disable rate limiter for tests ---
class DummyRedis:
    async def evalsha(self, *args, **kwargs):
        return 1

    async def script_load(self, *args, **kwargs):
        return "dummy-sha"

    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        return True

    async def incr(self, *args, **kwargs):
        return 1

    async def expire(self, *args, **kwargs):
        return True


@pytest.fixture(autouse=True)
def disable_limiter(monkeypatch):
    """
    Completely disable FastAPILimiter in tests.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: pytest.MonkeyPatch
    """
    FastAPILimiter.redis = DummyRedis()

    async def fake_identifier(request):
        return "test-client"

    async def fake_http_callback(request, response, pexpire):
        # Simply return the response without errors
        return response

    monkeypatch.setattr(FastAPILimiter, "identifier", fake_identifier)
    monkeypatch.setattr(FastAPILimiter, "http_callback", fake_http_callback)
