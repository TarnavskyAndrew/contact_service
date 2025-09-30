import asyncio
from sqlalchemy import select
from colorama import Fore, Style, init

from src.database.db import session
from src.database.models import User
from src.services.auth import auth_service
from src.conf.config import settings


# Init colorama
init(autoreset=True)

ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

MODERATOR_EMAIL = settings.MODERATOR_EMAIL
MODERATOR_PASSWORD = settings.MODERATOR_PASSWORD


async def create_admin_and_moderator():
    """
    Create an initial administrator and moderator account.

    - Admin credentials read from env (ADMIN_EMAIL, ADMIN_PASSWORD).
    - Moderator credentials read from env (MODERATOR_EMAIL, MODERATOR_PASSWORD),
      with defaults if not provided.

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
        # --- Admin ---
        res = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        admin = res.scalar_one_or_none()
        if not admin:
            pwd_hash = auth_service.get_password_hash(ADMIN_PASSWORD)
            admin = User(
                username="admin",
                email=ADMIN_EMAIL,
                password=pwd_hash,
                role="admin",
                confirmed=True,
            )
            db.add(admin)
            await db.commit()
            print(
                Fore.BLUE
                + f">>> Admin {ADMIN_EMAIL} created. Password: {ADMIN_PASSWORD}"
                + Style.RESET_ALL
            )
        else:
            print(
                Fore.GREEN
                + f">>> User {ADMIN_EMAIL} already exists (role={admin.role})"
                + Style.RESET_ALL
            )

        # --- Moderator ---
        res = await db.execute(select(User).where(User.email == MODERATOR_EMAIL))
        moderator = res.scalar_one_or_none()
        if not moderator:
            pwd_hash = auth_service.get_password_hash(MODERATOR_PASSWORD)
            moderator = User(
                username="moderator",
                email=MODERATOR_EMAIL,
                password=pwd_hash,
                role="moderator",
                confirmed=True,
            )
            db.add(moderator)
            await db.commit()
            print(
                Fore.BLUE
                + f">>> Moderator {MODERATOR_EMAIL} created. Password: {MODERATOR_PASSWORD}"
                + Style.RESET_ALL
            )
        else:
            print(
                Fore.GREEN
                + f">>> User {MODERATOR_EMAIL} already exists (role={moderator.role})"
                + Style.RESET_ALL
            )


if __name__ == "__main__":
    """
    CLI entry point for creating an administrator.

    Usage:
        poetry run python seed.py
    """
    asyncio.run(create_admin_and_moderator())


# poetry run python seed.py
