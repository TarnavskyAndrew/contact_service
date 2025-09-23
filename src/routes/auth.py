from datetime import datetime, timezone, timedelta
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Request,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError, ExpiredSignatureError

from src.database.db import get_db
from src.schemas import (
    SignupResponse,
    UserModel,
    UserResponse,
    TokenModel,
    RequestEmail,
    ResetPasswordModel,
    LoginRequest,
)
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


# --- SIGNUP ---
@router.post(
    "/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserModel,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    - Hashes the password.
    - Stores user in the database.
    - Sends a confirmation email with a verification token.

    :param body: New user data (username, email, password).
    :type body: UserModel
    :param request: Current request (used to build confirmation link).
    :type request: Request
    :param background_tasks: Background task manager for sending emails.
    :type background_tasks: BackgroundTasks
    :param db: Active database session.
    :type db: AsyncSession
    :raises HTTPException: 409 if user already exists.
    :return: Newly created user and message.
    :rtype: SignupResponse
    """

    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=409, detail="Account already exists")

    password_hash = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, password_hash, db)

    confirm_token = auth_service.create_email_token({"sub": new_user.email})
    confirm_link = f"{str(request.base_url)}api/auth/confirmed_email/{confirm_token}"

    background_tasks.add_task(
        send_email,
        new_user.email,
        new_user.username or "user",
        confirm_link,
        "email_template.html",
    )

    return SignupResponse(
        user=UserResponse.model_validate(new_user),
        detail="User created. Check your email.",
    )


# --- LOGIN ---
@router.post("/login", response_model=TokenModel)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    User login endpoint.

    Authentication flow:
        1. Look up user by email in the database.
        2. If not found → 401 Unauthorized ("Invalid email").
        3. If password mismatch → 401 Unauthorized ("Invalid password").
        4. If user exists but not confirmed → 403 Forbidden ("Email not confirmed").
        5. If success → issue access & refresh tokens, update DB.

    :param body: Validated login request payload.
    :type body: LoginRequest
    :param db: Active async database session.
    :type db: AsyncSession

    :raises HTTPException 401: If email not found or password invalid.
    :raises HTTPException 403: If email exists but not confirmed.
    :raises HTTPException 422: If request payload fails validation.

    :return: Access and refresh tokens with type.
    :rtype: TokenModel
    """

    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email not confirmed"
        )

    access = await auth_service.create_access_token(data={"sub": user.email})
    refresh = await auth_service.create_refresh_token(data={"sub": user.email})

    await repository_users.update_token(user, refresh, db)

    return TokenModel(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
    )


# --- LOGOUT ---
@router.post("/logout")
async def logout(
    user=Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Log out the current user.

    - Revokes the stored refresh token.

    :param user: Current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: Success message.
    :rtype: dict
    """

    await repository_users.update_token(user, None, db)  # refresh_token -> None
    return {"message": "Successfully logged out"}


# --- EMAIL CONFIRM ---
@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirm a user's email address.

    :param token: Confirmation JWT.
    :type token: str
    :param db: Active database session.
    :type db: AsyncSession
    :raises HTTPException: 400 if invalid token or user not found.
    :return: Confirmation status.
    :rtype: dict
    """

    email = await auth_service.get_email_from_token(
        token, expected_scope="email_verify"
    )
    user = await repository_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )

    if user.confirmed:
        return {"message": "Your email is already confirmed"}

    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


# --- RESEND CONFIRM EMAIL ---
@router.post("/resend_confirm_email")
async def resend_confirm_email(
    body: RequestEmail,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend confirmation email for unverified users.

    :param body: Email request payload.
    :type body: RequestEmail
    :param request: Current request (for confirmation link).
    :type request: Request
    :param background_tasks: Background task manager for sending emails.
    :type background_tasks: BackgroundTasks
    :param db: Active database session.
    :type db: AsyncSession
    :return: Message about resend status.
    :rtype: dict
    """

    user = await repository_users.get_user_by_email(body.email, db)

    # Не видаємо зайву інфу (якщо користувача немає - теж відповідаємо успіхом)
    if not user:
        return {"message": "If user exists, a confirmation email has been resent"}

    if user.confirmed:
        return {"message": "User already confirmed"}

    # create a new token
    confirm_token = auth_service.create_email_token({"sub": user.email})
    if isinstance(confirm_token, bytes):
        confirm_token = confirm_token.decode("utf-8")

    confirm_link = f"{str(request.base_url)}api/auth/confirmed_email/{confirm_token}"

    # we are sending a letter
    background_tasks.add_task(
        send_email,
        user.email,
        user.username or "user",
        confirm_link,
        "email_template.html",
    )

    return {"message": "Confirmation email resent. Check your inbox."}


# --- REFRESH TOKEN ---
@router.post("/refresh_token")
async def refresh_token(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Refresh access and refresh tokens using a valid refresh token.

    :param data: Request body containing ``refresh_token``.
    :type data: dict
    :param db: Active database session.
    :type db: AsyncSession
    :raises HTTPException:
        - 400 if refresh token missing.
        - 401 if refresh token invalid or does not match DB.
    :return: New access and refresh tokens.
    :rtype: dict
    """

    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing refresh token"
        )

    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = await repository_users.get_user_by_email(email, db)
    if user is None or user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    new_refresh_token = await auth_service.create_refresh_token(
        data={"sub": user.email}
    )

    await repository_users.update_token(user, new_refresh_token, db)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


# --- REQUEST RESET PASSWORD ---
@router.post("/request_reset_password")
async def request_reset_password(
    body: RequestEmail,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset.

    - Always responds success (so attackers cannot enumerate users).
    - If user exists → generates reset token and sends email.

    :param body: Email request payload.
    :type body: RequestEmail
    :param request: Current request (used to build reset link).
    :type request: Request
    :param background_tasks: Background task manager for sending emails.
    :type background_tasks: BackgroundTasks
    :param db: Active database session.
    :type db: AsyncSession
    :return: Message about reset status.
    :rtype: dict
    """

    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        return {"message": "If user exists, an email has been sent"}

    reset_token = jwt.encode(
        {
            "sub": user.email,
            "scope": "reset_password",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    reset_link = f"{str(request.base_url)}api/auth/reset_password/{reset_token}"
    # print("RESET LINK:", reset_link)

    background_tasks.add_task(
        send_email,
        user.email,
        user.username or "user",
        reset_link,
        "reset_password_template.html",
    )

    return {"message": "Check your email for password reset link."}


# --- RESET PASSWORD ---
@router.post("/reset_password/{token}")
async def reset_password(
    token: str,
    body: ResetPasswordModel,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset a user's password.

    :param token: JWT reset token.
    :type token: str
    :param body: New password payload.
    :type body: ResetPasswordModel
    :param db: Active database session.
    :type db: AsyncSession
    :raises HTTPException:
        - 401 if token invalid or expired.
        - 404 if user not found.
        - 500 if DB error occurs.
    :return: Success message.
    :rtype: dict
    """

    try:
        # print("Incoming token:", token)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # print("PAYLOAD:", payload)

        if payload.get("scope") != "reset_password":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope"
            )

        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

    except ExpiredSignatureError:
        # print("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except JWTError as e:
        # print("JWT error:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}"
        )

    try:
        user = await repository_users.get_user_by_email(email, db)
        # print("Found user:", user)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.password = auth_service.get_password_hash(body.new_password)
        # db.add(user)
        await db.commit()
        await db.refresh(user)

        # print("Password updated for", email)
    except Exception as e:
        # print("DB error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error: {str(e)}",
        )

    return {"message": "Password reset successful"}


# --- Email open tracking ---
# @router.get("/{username}")
# async def request_email(
#     username: str, response: Response, db: AsyncSession = Depends(get_db)
# ):
#     print("--------------------------------")
#     print(f"{username} зберігаємо що він відкрив email в БД")
#     print("--------------------------------")
#     return FileResponse(
#         "src/static/open_check.png",
#         media_type="image/png",
#         content_disposition_type="inline",
#     )
