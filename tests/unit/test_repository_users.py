import pytest
from sqlalchemy import select
from src.repository import users
from src.database.models import User


# Run with: pytest tests/unit/test_repository_users.py -v


@pytest.mark.asyncio
async def test_create_user(db_session, test_user_data):
    """
    Repository should create a new user.

    → expect persisted User with id, username, and email.
    """
    user = await users.create_user(test_user_data, "hashed_pwd", db_session)
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert isinstance(user.id, int)


@pytest.mark.asyncio
async def test_get_user_by_email_found(db_session, create_user_in_db):
    """
    Repository should return user if email exists.
    """
    result = await users.get_user_by_email("test@example.com", db_session)
    assert result is not None
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session):
    """
    Repository should return None if email not found.
    """
    result = await users.get_user_by_email("none@example.com", db_session)
    assert result is None


@pytest.mark.asyncio
async def test_update_token(db_session, create_user_in_db):
    """
    Repository should update user's refresh token.
    """
    await users.update_token(create_user_in_db, "refresh123", db_session)
    refreshed = await users.get_user_by_email(create_user_in_db.email, db_session)
    assert refreshed.refresh_token == "refresh123"


@pytest.mark.asyncio
async def test_set_role_success(db_session, create_user_in_db):
    """
    Repository should update user's role.
    """
    result = await users.set_role(create_user_in_db.id, "admin", db_session)
    assert result.role == "admin"


@pytest.mark.asyncio
async def test_set_role_not_found(db_session):
    """
    Repository should return None if user id not found.
    """
    result = await users.set_role(999, "admin", db_session)
    assert result is None


@pytest.mark.asyncio
async def test_list_users(db_session, create_user_in_db):
    """
    Repository should list all users.
    """
    result = await users.list_users(db_session)
    assert len(result) == 1
    assert result[0].email == "test@example.com"


@pytest.mark.asyncio
async def test_confirmed_email_success(db_session, create_user_in_db):
    """
    Repository should confirm user email if found.
    """
    result = await users.confirmed_email(create_user_in_db.email, db_session)
    assert result.confirmed is True


@pytest.mark.asyncio
async def test_confirmed_email_not_found(db_session):
    """
    Repository should return None if email not found.
    """
    result = await users.confirmed_email("none@example.com", db_session)
    assert result is None


@pytest.mark.asyncio
async def test_update_avatar(db_session, create_user_in_db):
    """
    Repository should update user's avatar URL.
    """
    result = await users.update_avatar(
        create_user_in_db.email, "http://avatar", db_session
    )
    assert result.avatar == "http://avatar"


@pytest.mark.asyncio
async def test_update_password(db_session, create_user_in_db):
    """
    Repository should update user's password hash.
    """
    result = await users.update_password(create_user_in_db, "new_hashed", db_session)
    assert result.password == "new_hashed"
