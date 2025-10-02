import asyncio
from sqlalchemy import select
from colorama import Fore, Style, init
from faker import Faker

from src.database.db import session
from src.database.models import User, Contact
from src.services.auth import auth_service
from src.conf.config import settings


# Init colorama
init(autoreset=True)
fake = Faker()

ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

MODERATOR_EMAIL = settings.MODERATOR_EMAIL
MODERATOR_PASSWORD = settings.MODERATOR_PASSWORD

USER_EMAIL = settings.USER_EMAIL
USER_PASSWORD = settings.USER_PASSWORD


async def create_admin_and_moderator():
    """
    Create admin, moderator, and test user with 150 contacts.

    - Admin credentials read from env (ADMIN_EMAIL, ADMIN_PASSWORD).
    - User credentials read from env (USER_EMAIL, USER_PASSWORD).
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

            # --- Test User ---
        res = await db.execute(select(User).where(User.email == USER_EMAIL))
        test_user = res.scalar_one_or_none()
        if not test_user:
            pwd_hash = auth_service.get_password_hash(USER_PASSWORD)
            test_user = User(
                username="test_user",
                email=USER_EMAIL,
                password=pwd_hash,
                role="user",
                confirmed=True,
            )
            db.add(test_user)
            await db.commit()
            print(Fore.BLUE + f">>> Test user {USER_EMAIL} created." + Style.RESET_ALL)
        else:
            print(
                Fore.GREEN
                + f">>> Test user {USER_EMAIL} already exists."
                + Style.RESET_ALL
            )

        # --- helper for generating a valid phone number ---
        def generate_phone() -> str:
            """
            Generate Ukrainian phone number in strict format +380XXXXXXXXX.
            Always 9 digits after +380.
            """
            digits = "".join(str(fake.random_int(0, 9)) for _ in range(9))
            return "+380" + digits

        # --- Generate 150 Contacts for test user ---
        res = await db.execute(select(Contact).where(Contact.user_id == test_user.id))
        existing_contacts = res.scalars().all()

        if len(existing_contacts) < 150:
            to_add = 150 - len(existing_contacts)
            contacts = []
            for _ in range(to_add):
                contacts.append(
                    Contact(
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        email=fake.unique.email(),
                        phone=generate_phone(),
                        birthday=fake.date_of_birth(minimum_age=18, maximum_age=90),
                        extra=fake.word(),
                        user_id=test_user.id,
                    )
                )
            db.add_all(contacts)
            await db.commit()
            print(
                Fore.BLUE
                + f">>> Added {to_add} contacts for {USER_EMAIL}"
                + Style.RESET_ALL
            )
        else:
            print(
                Fore.GREEN
                + f">>> User {USER_EMAIL} already has {len(existing_contacts)} contacts."
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
