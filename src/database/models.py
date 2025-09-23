from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, func, Boolean


class Base(DeclarativeBase):
    """
    Declarative base class for SQLAlchemy models.

    All ORM models in the project inherit from this base class.
    """
    pass


class User(Base):

    """
    Database model for application user.

    :ivar id: Primary key.
    :vartype id: int
    :ivar username: Username (nullable, 2–32 characters).
    :vartype username: str | None
    :ivar email: User email address (unique).
    :vartype email: str
    :ivar password: Hashed password.
    :vartype password: str
    :ivar created_at: Timestamp of creation.
    :vartype created_at: datetime
    :ivar avatar: Avatar URL.
    :vartype avatar: str | None
    :ivar confirmed: Whether the email is confirmed.
    :vartype confirmed: bool
    :ivar role: User role (e.g. "user", "admin").
    :vartype role: str
    :ivar refresh_token: Refresh token for authentication.
    :vartype refresh_token: str | None
    :ivar contacts: Relationship to user's contacts.
    :vartype contacts: list[Contact]
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(25))
    email: Mapped[str] = mapped_column(
        String(250), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="user")

    contacts: Mapped[List["Contact"]] = relationship(
        back_populates="user", cascade="all,delete"
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)


class Contact(Base):

    """
    Database model for user contact.

    :ivar id: Primary key.
    :vartype id: int
    :ivar first_name: Contact's first name.
    :vartype first_name: str
    :ivar last_name: Contact's last name.
    :vartype last_name: str
    :ivar email: Contact email address.
    :vartype email: str
    :ivar phone: Contact phone number.
    :vartype phone: str
    :ivar birthday: Contact birthday date.
    :vartype birthday: date
    :ivar extra: Optional extra information.
    :vartype extra: str | None
    :ivar created_at: Timestamp of creation.
    :vartype created_at: datetime
    :ivar updated_at: Timestamp of last update.
    :vartype updated_at: datetime
    :ivar user_id: Foreign key to related user.
    :vartype user_id: int
    :ivar user: Relationship to the owning user.
    :vartype user: User
    """

    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(25), nullable=False)
    last_name: Mapped[str] = mapped_column(String(25), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    extra: Mapped[Optional[str]] = mapped_column(String(250))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship(back_populates="contacts")
