from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    """
    Retrieve a user by their email address.

    :param email: User email to search for.
    :type email: str
    :param db: Active database session.
    :type db: AsyncSession
    :return: User object if found, else None.
    :rtype: User | None
    """

    res = await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    return res.scalar_one_or_none()


async def create_user(body: UserModel, password_hash: str, db: AsyncSession) -> User:
    """
    Create a new user.

    :param body: Input data containing username, email, and plain password.
    :type body: UserModel
    :param password_hash: Hashed password to store in DB.
    :type password_hash: str
    :param db: Active database session.
    :type db: AsyncSession
    :return: Newly created user.
    :rtype: User
    """

    user = User(username=body.username, email=body.email, password=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_token(user: User, token: Optional[str], db: AsyncSession) -> None:
    """
    Update the refresh token for a given user.

    :param user: User object.
    :type user: User
    :param token: New refresh token or None (to revoke).
    :type token: str | None
    :param db: Active database session.
    :type db: AsyncSession
    :return: None
    :rtype: None
    """

    await db.execute(update(User).where(User.id == user.id).values(refresh_token=token))
    await db.commit()


async def set_role(user_id: int, role: str, db: AsyncSession) -> Optional[User]:
    """
    Update the role of a user.

    :param user_id: User identifier.
    :type user_id: int
    :param role: New role value (e.g., "admin", "user").
    :type role: str
    :param db: Active database session.
    :type db: AsyncSession
    :return: Updated user if found, else None.
    :rtype: User | None
    """

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        return None

    user.role = role
    db.add(user)  # <--
    await db.commit()
    await db.refresh(user)
    return user


async def list_users(db: AsyncSession) -> list[User]:
    """
    Retrieve all users ordered by ID.

    :param db: Active database session.
    :type db: AsyncSession
    :return: List of users.
    :rtype: list[User]
    """

    res = await db.execute(select(User).order_by(User.id))
    return list(res.scalars().all())


async def confirmed_email(email: str, db: AsyncSession) -> Optional[User]:
    """
    Mark a user's email as confirmed.

    :param email: User email.
    :type email: str
    :param db: Active database session.
    :type db: AsyncSession
    :return: Updated user if found, else None.
    :rtype: User | None
    """

    user = await get_user_by_email(email, db)
    if user:
        user.confirmed = True
        await db.commit()
        await db.refresh(user)
        return user
    return None


async def update_avatar(email, url: str, db: AsyncSession) -> User:
    """
    Update the avatar URL of a user.

    :param email: User email to identify user.
    :type email: str
    :param url: New avatar URL (Cloudinary link).
    :type url: str
    :param db: Active database session.
    :type db: AsyncSession
    :return: Updated user.
    :rtype: User
    """

    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(user: User, hashed_password: str, db: AsyncSession) -> User:
    """
    Update the password hash for a given user.

    :param user: User object.
    :type user: User
    :param hashed_password: New password hash.
    :type hashed_password: str
    :param db: Active database session.
    :type db: AsyncSession
    :return: Updated user.
    :rtype: User
    """

    user.password = hashed_password
    await db.commit()
    await db.refresh(user)
    return user
