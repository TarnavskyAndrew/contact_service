from typing import Any, Optional
from pydantic import ConfigDict, field_validator, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Global project settings.

    This class loads configuration variables from environment (via Pydantic v2),
    validates them, and provides convenience properties for database URLs.
    """

    # --- Database (строки) ---
    DATABASE_URL: Optional[str] = None
    # SYNC_DATABASE_URL: Optional[str] = None

    # --- Database (якщо строк немає) ---
    PG_DB_NAME: Optional[str] = None
    PG_USER: Optional[str] = None
    PG_PASSWORD: Optional[str] = None
    PG_PORT: Optional[int] = None
    PG_DOMAIN: Optional[str] = None

    # --- JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_EXPIRE_MIN: int = 15
    REFRESH_EXPIRE_DAYS: int = 7

    # --- Admin, User and Moderator (seed.py) ---
    ADMIN_EMAIL: EmailStr
    ADMIN_PASSWORD: str
    MODERATOR_EMAIL: EmailStr
    MODERATOR_PASSWORD: str
    USER_EMAIL: EmailStr
    USER_PASSWORD: str

    # --- SMTP ---
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 2525
    MAIL_SERVER: str

    # Чи логувати листи у файл (tmp_emails/) при успішному надсиланні
    DEBUG_EMAILS: bool = True

    # --- Cloudinary ---
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- PGAdmin ---
    PGADMIN_DEFAULT_EMAIL: str
    PGADMIN_DEFAULT_PASSWORD: str

    # --- FastAPI Testing Token Check ---
    TEST_PROTECTED_PATH: str = "/api/contacts/"

    # --- Pydantic v2 config ---
    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )  # type: ignore

    # --- Validators ---
    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: Any):
        if v not in ["HS256", "HS512"]:
            raise ValueError("ALGORITHM must be HS256 or HS512")
        return v

    # --- Properties для строк ---
    @property
    # Async url for SQLAlchemy (asyncpg)
    def async_db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if all(
            [
                self.PG_USER,
                self.PG_PASSWORD,
                self.PG_DOMAIN,
                self.PG_PORT,
                self.PG_DB_NAME,
            ]
        ):
            return (
                f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}"
                f"@{self.PG_DOMAIN}:{self.PG_PORT}/{self.PG_DB_NAME}"
            )
        raise ValueError("DATABASE_URL or PG_* variables must be set")

    @property
    # Sinc url for Alembic (psycopg2)
    def sync_db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        if all(
            [
                self.PG_USER,
                self.PG_PASSWORD,
                self.PG_DOMAIN,
                self.PG_PORT,
                self.PG_DB_NAME,
            ]
        ):
            return (
                f"postgresql+psycopg2://{self.PG_USER}:{self.PG_PASSWORD}"
                f"@{self.PG_DOMAIN}:{self.PG_PORT}/{self.PG_DB_NAME}"
            )
        raise ValueError("DATABASE_URL or PG_* variables must be set")


settings = Settings()
