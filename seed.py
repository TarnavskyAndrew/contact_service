import asyncio
from sqlalchemy import select

from src.database.db import session
from src.database.models import User
from src.services.auth import auth_service
from src.conf.config import settings


ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD


async def create_admin():
    """
    Create an initial administrator account.

    This script is intended to be run on first project startup
    to ensure there is at least one admin user in the database.

    - Reads credentials from environment variables ``ADMIN_EMAIL`` and ``ADMIN_PASSWORD``.
    - Verifies if a user with the same email already exists.
    - If not, creates a new user with role ``admin``.

    :raises ValueError: If required environment variables are missing.
    :return: None
    :rtype: None

    Example:
        >>> poetry run python seed.py
        Admin admin@example.com created. Password: secret123
    """
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise ValueError("Please set ADMIN_EMAIL and ADMIN_PASSWORD in .env")

    async with session() as db:
        res = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = res.scalar_one_or_none()

        if user:
            print(f"User {ADMIN_EMAIL} already exists (role={user.role})")
            return

        pwd_hash = auth_service.get_password_hash(ADMIN_PASSWORD)
        admin = User(
            username="admin", email=ADMIN_EMAIL, password=pwd_hash, role="admin"
        )
        db.add(admin)
        await db.commit()
        print(f"Admin {ADMIN_EMAIL} created. Password: {ADMIN_PASSWORD}")



if __name__ == "__main__":
    """
    CLI entry point for creating an administrator.

    Usage:
        poetry run python seed.py
    """
    asyncio.run(create_admin())


# poetry run python seed.py
