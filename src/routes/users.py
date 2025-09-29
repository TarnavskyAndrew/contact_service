from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import cloudinary, cloudinary.uploader

from src.database.db import get_db
from src.database.models import User
from src.schemas import RoleUpdate, UserDb
from src.repository.users import list_users, set_role
from src.services.permissions import access_admin_only, Role
from src.services.auth import auth_service
from src.services.storage import upload_avatar
from src.conf.config import settings
from src.repository import users as repository_users
from src.utils.validate_file_size import validate_file_size


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserDb], dependencies=[Depends(access_admin_only)])
async def get_users(db: AsyncSession = Depends(get_db)):
    """
    Get a list of all users (admin only).

    :param db: Active database session.
    :type db: AsyncSession
    :return: List of users with basic profile info.
    :rtype: list[UserDb]

    Example response::

        [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "created_at": "2025-09-09T12:00:00",
                "avatar": null,
                "role": "admin"
            }
        ]
    """

    return await list_users(db)


@router.patch(
    "/{user_id}/role",
    summary="Change user role (Available only for admin)",
    response_model=UserDb,
    dependencies=[Depends(access_admin_only)],
)
async def change_role(
    user_id: int, body: RoleUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Change a user's role (admin only).

    :param user_id: User ID to update.
    :type user_id: int
    :param body: New role value (e.g. ``admin``, ``user``, ``moderator``).
    :type body: RoleUpdate
    :param db: Active database session.
    :type db: AsyncSession
    :raises HTTPException: 404 if user not found.
    :return: Updated user with new role.
    :rtype: UserDb
    """

    user = await repository_users.set_role(user_id, body.role, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/avatar", status_code=200)
async def update_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current: User = Depends(auth_service.get_current_user),
):
    """
    Upload and update the current user's avatar (simple variant).

    - Accepts only images (png, jpeg, jpg, webp).
    - Stores avatar via Cloudinary (configured in ``storage.py``).
    - Saves URL to user's record.

    :param file: Image file to upload.
    :type file: UploadFile
    :param db: Active database session.
    :type db: AsyncSession
    :param current: Current authenticated user.
    :type current: User
    :raises HTTPException: 415 if unsupported file type.
    :return: JSON with avatar URL.
    :rtype: dict
    """

    await validate_file_size(file)  # validate file size (max 2 MB)

    if file.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise HTTPException(status_code=415, detail="Unsupported media type")
    url = await upload_avatar(file.file, public_id=f"ContactsAPI/{current.username}")
    current.avatar = url
    await db.commit()
    return {"avatar_url": url}


@router.patch("/avatar", response_model=UserDb)
async def update_avatar_user(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and update the current user's avatar (advanced Cloudinary variant).

    - Uses Cloudinary uploader directly.
    - Overwrites existing avatar.
    - Builds URL with resizing (250x250, crop=fill).

    :param file: Image file to upload.
    :type file: UploadFile
    :param current_user: Current authenticated user.
    :type current_user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: Updated user object with new avatar URL.
    :rtype: UserDb
    """

    await validate_file_size(file)  # validate file size (max 2 MB)

    if file.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise HTTPException(status_code=415, detail="Unsupported media type")

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    r = cloudinary.uploader.upload(
        file.file, public_id=f"ContactsAPI/{current_user.username}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(
        f"ContactsAPI/{current_user.username}"
    ).build_url(width=250, height=250, crop="fill", version=r.get("version"))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
