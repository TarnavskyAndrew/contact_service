from pydantic import BaseModel, EmailStr, Field, field_validator, constr
from typing import Optional, List, Literal
from datetime import date, datetime
import re

from src.models.roles import Role


EMAIL_REGEX = re.compile(
    r"^(?![.-])"  # local-part не починається з . або -
    r"(?!.*\.\.)"  # немає подвійних точок в local-part
    r"[a-zA-Z0-9._%+-]{1,64}"  # local-part (1–64 символи)
    r"(?<![.-])"  # local-part не закінчується . або -
    r"@"
    r"(?!-)"  # домен не починається з -
    r"(?!.*\.\.)"  # немає подвійних точок у домені
    r"[A-Za-z0-9.-]{1,253}"  # domain part
    r"(?<!-)"  # домен не закінчується на -
    r"\.[A-Za-z]{2,}$"  # TLD мінімум 2 літери
)

USERNAME_REGEX = re.compile(
    r"^(?![.\-_])"  # не починається з ., -, _
    r"(?!.*[.\-_]{2,})"  # немає підряд двох і більше спецсимволів
    r"(?!\d+$)"  # не тільки цифри
    r"[A-Za-z0-9.\-_]{2,32}"  # латиниця, цифри, ., -, _
    r"(?<![.\-_])$"  # не закінчується на ., -, _
)


# # -------- USER ----------
# class UserModel(BaseModel):
#     """
#     Schema for user registration input.

#     :ivar username: Optional username (2 - 32 chars).
#     :vartype username: str | None
#     :ivar email: User email address.
#     :vartype email: EmailStr
#     :ivar password: Plaintext password (6 - 64 chars).
#     :vartype password: str
#     """

#     username: Optional[str] = Field(default=None, min_length=2, max_length=32)
#     email: EmailStr
#     password: str = Field(min_length=6, max_length=64)


# -------- USER ----------
class UserModel(BaseModel):
    """
    Schema for user registration (/auth/signup).

    Fields:
        username (str | None): Optional username, 2–32 characters.
        email (str): User email, validated and normalized.
        password (str): User password, 6–64 characters.

    Email validation rules:
        - Minimum length = 6.
        - Maximum total length = 254 characters.
        - Local-part (before @) ≤ 64 characters.
        - Cannot start or end with '.' or '-'.
        - No consecutive dots.
        - Domain cannot start or end with '-'.
        - Domain part ≤ 253 characters.
        - TLD must be ≥ 2 letters.

    Password validation rules:
        - Minimum length = 6.
        - Maximum length = 64.
        - Cannot consist only of spaces.
        - TODO: At least one uppercase
        - TODO: At least one lowercase
        - TODO: At least one digit
        - TODO: At least one special character
        - TODO: Not a common weak password
        - TODO: Not equal to username or email

    Username validation rules:
        - Length = 2–32 characters.
        - TODO: Only letters, numbers, `_ . -`.
        - TODO: Cannot start/end with `.` / `-` / `_`.
        - TODO: No consecutive special symbols (`..`, `__`, etc.).
        - TODO: No only digits.
    """

    username: str | None = Field(default=None, min_length=2, max_length=32)
    # email: str = Field(min_length=6, max_length=254)
    email: str
    password: str = Field(min_length=6, max_length=64)

    # USERNAME VALIDATION
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Validate username format. TODO: enforce strict regex rules."""

        if v is None:
            return v

        # TODO: Strict regex validation
        # if not USERNAME_REGEX.match(v):
        #     raise ValueError("Invalid username format")

        return v

    # EMAIL VALIDATION
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email according to defined rules."""
        v = v.strip()

        # 1. Check total length
        if len(v) < 6:
            raise ValueError("Email too short")

        # 2. Check total length
        if len(v) > 254:
            raise ValueError("Email too long")

        # 3. Split local and domain parts
        local, _, domain = v.partition("@")

        # 4. Check local-part length
        if len(local) > 64:
            raise ValueError("Local part too long")

        # 5. Regex validation (syntax check)
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")

        return v

    # PASSWORD VALIDATION
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        """Ensure password is not only spaces. TODO: add stronger validation rules."""
        if v.strip() == "":
            raise ValueError("Password cannot be only spaces")

        # TODO: Enforce minimum length = 6 (already handled by Field)
        # if len(v) < 6 or len(v) > 64:
        #     raise ValueError("Password length must be 6–64 characters")

        # TODO: Require at least one uppercase
        # if not any(c.isupper() for c in v):
        #     raise ValueError("Password must contain at least one uppercase letter")

        # TODO: Require at least one lowercase
        # if not any(c.islower() for c in v):
        #     raise ValueError("Password must contain at least one lowercase letter")

        # TODO: Require at least one digit
        # if not any(c.isdigit() for c in v):
        #     raise ValueError("Password must contain at least one digit")

        # TODO: Require at least one special character
        # if not any(c in "!@#$%^&*()-_=+[]{};:,.<>?/|\\`~" for c in v):
        #     raise ValueError("Password must contain at least one special character")

        # TODO: Check against common weak passwords
        # COMMON_PASSWORDS = {"password", "123456", "qwerty", "letmein", "admin"}
        # if v.lower() in COMMON_PASSWORDS:
        #     raise ValueError("Password is too common")

        # TODO: Prevent matching username or email
        # if "username" in info.data and v.lower() == str(info.data["username"]).lower():
        #     raise ValueError("Password cannot match username")
        # if "email" in info.data and v.lower() == str(info.data["email"]).lower():
        #     raise ValueError("Password cannot match email")

        return v


class UserDb(BaseModel):
    """
    Schema for user data stored in database (read-only).

    :ivar id: User ID.
    :vartype id: int
    :ivar username: Username.
    :vartype username: str | None
    :ivar email: User email.
    :vartype email: EmailStr
    :ivar created_at: Timestamp of creation.
    :vartype created_at: datetime
    :ivar avatar: Avatar URL.
    :vartype avatar: str | None
    :ivar role: User role (e.g. "user", "admin").
    :vartype role: str
    """

    id: int
    username: Optional[str]
    email: EmailStr
    created_at: datetime
    avatar: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """
    Schema for user response returned by API.

    :ivar id: User ID (optional).
    :vartype id: int | None
    :ivar username: Username.
    :vartype username: str
    :ivar email: Email address.
    :vartype email: EmailStr
    :ivar created_at: Creation timestamp.
    :vartype created_at: datetime | None
    :ivar avatar: Avatar URL.
    :vartype avatar: str | None
    :ivar role: User role.
    :vartype role: str | None
    :ivar confirmed: Whether email is confirmed.
    :vartype confirmed: bool | None
    """

    id: int | None = None
    username: str
    email: EmailStr
    created_at: datetime | None = None
    avatar: str | None = None
    role: str | None = None
    confirmed: bool | None = None

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    """
    Schema for updating a user's role.

    :ivar role: New role value. Must be one of: "admin", "moderator", "user".
    :vartype role: Role
    """

    role: Role


# --------- AUTH ---------
class SignupResponse(BaseModel):
    """
    Schema for signup response.

    :ivar user: User object.
    :vartype user: UserResponse
    :ivar detail: Status message.
    :vartype detail: str
    """

    user: UserResponse
    detail: str = "User created. Check your email."


class TokenModel(BaseModel):
    """
    Schema for authentication tokens.

    :ivar access_token: Short-lived access token.
    :vartype access_token: str
    :ivar refresh_token: Long-lived refresh token.
    :vartype refresh_token: str
    :ivar token_type: Token type (default = "bearer").
    :vartype token_type: str
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """
    Schema for requests that require only email.

    :ivar email: Email address.
    :vartype email: EmailStr

    Example::

        {"email": "user@example.com"}
    """

    email: EmailStr

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com"}}}


class ResetPasswordModel(BaseModel):
    """
    Schema for reset password request.

    :ivar new_password: New password to set.
    :vartype new_password: str
    """

    new_password: str


# -------- CONTACT ----------
class ContactBase(BaseModel):
    """
    Base schema for contact data.

    :ivar first_name: Contact's first name (1–25 characters, only letters and - . _ ').
    :vartype first_name: str
    :ivar last_name: Contact's last name (1–25 characters, only letters and - . _ ').
    :vartype last_name: str
    :ivar email: Contact's email address (valid, ≤100 chars).
    :vartype email: EmailStr
    :ivar phone: Contact's phone number (5–20 digits, optional + at start).
    :vartype phone: str
    :ivar birthday: Contact's birthday (must not be in the future).
    :vartype birthday: date
    :ivar extra: Optional extra information (≤250 chars).
    :vartype extra: str | None
    """

    first_name: constr(
        pattern=r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ][A-Za-zА-Яа-яЁёІіЇїЄєҐґ\-\._']{0,24}$"
    ) = Field(..., description="First name: 1–25 chars, letters + - . _ ' allowed")
    last_name: constr(
        pattern=r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ][A-Za-zА-Яа-яЁёІіЇїЄєҐґ\-\._']{0,24}$"
    ) = Field(..., description="Last name: 1–25 chars, letters + - . _ ' allowed")
    email: EmailStr = Field(
        ..., max_length=100, description="Valid unique email, max 100 chars"
    )
    phone: str = Field(
        ..., description="Phone number: E.164 format, stricter rules for UA (+380)"
    )
    birthday: date
    extra: Optional[constr(max_length=250)] = Field(
        None, description="Extra info, max 250 chars"
    )

    # --- Custom validators ---
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # if number doesn't start with + → add it
        if not v.startswith("+"):
            v = "+" + v

        # Special rule for Ukraine
        if v.startswith("+380"):
            digits = v[4:]
            if len(digits) != 9:
                raise ValueError("Ukrainian phone must be in format +380XXXXXXXXX")
            if not digits.isdigit():
                raise ValueError("Ukrainian phone must contain only digits")
        else:
            # For other countries, check E.164 (8–15 digits total, including country code)
            digits = v[1:]
            if not digits.isdigit():
                raise ValueError("Phone must contain digits only")
            if digits[0] == "0":
                raise ValueError("Country code cannot start with 0 (E.164 rule)")
            if not (8 <= len(digits) <= 15):
                raise ValueError("Phone must follow E.164 format (+CountryCodeNumber)")

        return v

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Birthday cannot be in the future")
        return v


class ContactCreate(ContactBase):
    """
    Schema for creating a new contact.

    Inherits all fields from ContactBase.

    :rtype: ContactCreate
    """

    pass


class ContactUpdate(BaseModel):
    """
    Schema for updating contact data.
    All fields optional, but validated with same constraints.

    :ivar first_name: Contact's first name (1–25 characters, only letters and - . _ ').
    :vartype first_name: str | None
    :ivar last_name: Contact's last name (1–25 characters, only letters and - . _ ').
    :vartype last_name: str | None
    :ivar email: Contact email (valid, ≤100 chars).
    :vartype email: EmailStr | None
    :ivar phone: Contact's phone number (5–20 characters).
    :vartype phone: str | None
    :ivar birthday: Contact's birthday.
    :vartype birthday: date | None
    :ivar extra: Optional extra information (≤250 chars).
    :vartype extra: str | None
    """

    first_name: Optional[
        constr(
            pattern=r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ][A-Za-zА-Яа-яЁёІіЇїЄєҐґ\-\._']{0,24}$"
        )
    ]
    last_name: Optional[
        constr(
            pattern=r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ][A-Za-zА-Яа-яЁёІіЇїЄєҐґ\-\._']{0,24}$"
        )
    ]
    email: Optional[EmailStr] = Field(None, max_length=100)
    phone: Optional[str] = Field(
        None,
        description="Phone number: auto-add + if missing, must follow E.164 format",
    )
    birthday: Optional[date]
    extra: Optional[constr(max_length=250)]

    # --- Custom validators ---
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # if number doesn't start with + → add it
        if not v.startswith("+"):
            v = "+" + v

        # Special rule for Ukraine
        if v.startswith("+380"):
            digits = v[4:]
            if len(digits) != 9:
                raise ValueError("Ukrainian phone must be in format +380XXXXXXXXX")
            if not digits.isdigit():
                raise ValueError("Ukrainian phone must contain only digits")
        else:
            # For other countries, check E.164 (8–15 digits total, including country code)
            digits = v[1:]
            if not digits.isdigit():
                raise ValueError("Phone must contain digits only")
            if digits[0] == "0":
                raise ValueError("Country code cannot start with 0 (E.164 rule)")
            if not (8 <= len(digits) <= 15):
                raise ValueError("Phone must follow E.164 format (+CountryCodeNumber)")

        return v

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Birthday cannot be in the future")
        return v


class ContactResponse(ContactBase):
    """
    Schema for contact response (includes ID).

    :ivar id: Contact ID.
    :vartype id: int
    """

    id: int

    class Config:
        from_attributes = True


# -------- DEBUG ----------
class DebugEmailRequest(BaseModel):
    """
    Schema for debug email request.

    :ivar email: Recipient email.
    :vartype email: EmailStr
    """

    email: EmailStr


# -------- LOGIN ----------
# class LoginRequest(BaseModel):
#     """
#     Schema for user login request.

#     :ivar email: User login email (RFC 5321).
#     :vartype email: EmailStr
#     :ivar password: User password.
#     :vartype password: str
#     """

#     email: EmailStr = Field(
#         ..., min_length=6, max_length=254, description="Valid email required"
#     )
#     password: str = Field(
#         ..., min_length=6, max_length=128, description="Password min 6, max 128"
#     )


# -------- LOGIN ----------
class LoginRequest(BaseModel):
    """
    Schema for user login (/auth/login).

    :param email: User email, validated and normalized.
    :type email: str
    :param password: User password (6–128 characters).
    :type password: str
    """

    email: str
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Normalize and validate email.

        - Strips spaces before validation.
        - Validates with EMAIL_REGEX.
        - Raises ValueError if invalid.
        """
        v = v.strip()  # <--- fix
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v
