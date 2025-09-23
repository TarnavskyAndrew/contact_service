from datetime import datetime, timedelta, timezone
from typing import Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users


# --- crypto / oauth2 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """
    Service class for authentication and authorization.

    Provides functionality for:
    - Password hashing and verification.
    - JWT creation (access, refresh, email verification, reset).
    - JWT decoding and validation.
    - Retrieving current user from token.
    """

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_EXPIRE_MIN
        self.refresh_token_expire_days = settings.REFRESH_EXPIRE_DAYS

    # --- PASSWORD ---
    def get_password_hash(self, password: str) -> str:
        """
        Hash a plain password using bcrypt.

        :param password: Plaintext password.
        :type password: str
        :return: Hashed password string.
        :rtype: str
        """

        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hash.

        :param plain_password: Plaintext password.
        :type plain_password: str
        :param hashed_password: Stored password hash.
        :type hashed_password: str
        :return: True if password matches, else False.
        :rtype: bool
        """

        return pwd_context.verify(plain_password, hashed_password)

    # --- TOKEN HELPERS ---
    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        """
        Create a JWT token with expiration.

        :param data: Payload to encode (e.g., {"sub": email}).
        :type data: dict
        :param expires_delta: Expiration delta.
        :type expires_delta: timedelta
        :return: Encoded JWT string.
        :rtype: str
        """

        # to_encode = data.copy()
        # expire = datetime.now(timezone.utc) + expires_delta
        # to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        # token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        # return token

        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        to_encode.update(
            {
                "exp": expire,
                "iat": now,
                "jti": str(uuid4()),  # унікальний id токена, завжди різний
            }
        )
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    async def create_access_token(self, data: dict) -> str:
        """
        Create a short-lived access token.

        :param data: Payload (must include "sub" = email).
        :type data: dict
        :return: Encoded access token.
        :rtype: str
        """

        return self._create_token(
            data, timedelta(minutes=self.access_token_expire_minutes)
        )

    async def create_refresh_token(self, data: dict) -> str:
        """
        Create a long-lived refresh token.

        :param data: Payload (must include "sub" = email).
        :type data: dict
        :return: Encoded refresh token.
        :rtype: str
        """

        return self._create_token(data, timedelta(days=self.refresh_token_expire_days))

    def create_email_token(self, data: dict) -> str:
        """
        Create a verification token for email confirmation.

        :param data: Payload (must include "sub" = email).
        :type data: dict
        :return: Encoded email verification token (valid 24h).
        :rtype: str
        """

        data.update({"scope": "email_verify"})
        return self._create_token(data, timedelta(hours=24))

    def create_reset_token(self, data: dict) -> str:
        """
        Create a password reset token.

        :param data: Payload (must include "sub" = email).
        :type data: dict
        :return: Encoded reset token (valid 1h).
        :rtype: str
        """

        data.update({"scope": "reset_password"})
        return self._create_token(data, timedelta(hours=1))

    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate a JWT token.

        :param token: Encoded JWT string.
        :type token: str
        :raises HTTPException: 401 if token expired or invalid.
        :return: Decoded payload dictionary.
        :rtype: dict
        """

        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    # --- CURRENT USER ---
    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ) -> User:
        """
        Retrieve the current user from the JWT access token.

        :param token: JWT access token (in Authorization header).
        :type token: str
        :param db: Active database session.
        :type db: AsyncSession
        :raises HTTPException: 401 if token invalid or user not found.
        :return: User object.
        :rtype: User
        """

        payload = self.decode_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user

    async def get_email_from_token(self, token: str, expected_scope: str) -> str:
        """
        Extract email from a token with scope validation.

        :param token: Encoded JWT token.
        :type token: str
        :param expected_scope: Expected scope value (e.g., "email_verify", "reset_password").
        :type expected_scope: str
        :raises HTTPException:
            - 400 if scope mismatch or invalid payload.
            - 400 if token expired or invalid.
        :return: Email from token.
        :rtype: str
        """

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("scope") != expected_scope:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token scope",
                )
            email = payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token payload",
                )
            return email
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )


#: Global instance of AuthService to be used in routes and dependencies.
auth_service = AuthService()
