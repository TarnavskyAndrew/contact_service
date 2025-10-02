from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.repository import contacts as repo_contacts
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.database.models import User
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/",
    response_model=List[ContactResponse],
    dependencies=[Depends(RateLimiter(times=50, seconds=60))],
)  # ≤100 requests per minute
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get a paginated list of contacts for the current user.

    :param skip: Number of records to skip.
    :type skip: int
    :param limit: Maximum number of records to return (1–100).
    :type limit: int
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :return: List of contacts.
    :rtype: list[ContactResponse]
    """

    return await repo_contacts.get_contacts(skip, limit, current_user, db)


@router.get(
    "/search",
    response_model=List[ContactResponse],
    dependencies=[
        Depends(RateLimiter(times=50, seconds=60))
    ],  # ≤50 requests per minute
)
async def search_contacts(
    q: str = Query(..., description="Search by first name, last name, or email"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Search contacts by name or email.

    :param q: Query string (matches first name, last name, or email).
    :type q: str
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :return: List of matching contacts.
    :rtype: list[ContactResponse]
    """

    return await repo_contacts.search_contacts(q, current_user, db)


@router.get("/upcoming-birthdays", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get contacts with birthdays within the next N days.

    :param days: Number of days to look ahead (default = 7).
    :type days: int
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :return: List of contacts with upcoming birthdays.
    :rtype: list[ContactResponse]
    """

    return await repo_contacts.get_upcoming_birthdays(days, current_user, db)


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    dependencies=[
        Depends(RateLimiter(times=50, seconds=60))
    ],  # ≤50 requests per minute
)
async def get_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get a single contact by ID.

    :param contact_id: Contact ID.
    :type contact_id: int
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :raises HTTPException: 404 if contact not found.
    :return: Contact details.
    :rtype: ContactResponse
    """
    contact = await repo_contacts.get_contact(contact_id, current_user, db)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(RateLimiter(times=25, seconds=60))
    ],  # ≤25 requests per minute
)
# @router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Create a new contact.

    :param body: Contact creation payload.
    :type body: ContactCreate
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :return: Newly created contact.
    :rtype: ContactResponse
    """
    return await repo_contacts.create_contact(body, current_user, db)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactUpdate,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Update an existing contact.

    :param body: Contact update payload.
    :type body: ContactUpdate
    :param contact_id: Contact ID.
    :type contact_id: int
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :raises HTTPException: 404 if contact not found.
    :return: Updated contact.
    :rtype: ContactResponse
    """
    contact = await repo_contacts.update_contact(contact_id, body, current_user, db)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],  # ≤5 requests per minute
)
async def delete_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Delete a contact by ID.

    :param contact_id: Contact ID.
    :type contact_id: int
    :param db: Active database session.
    :type db: AsyncSession
    :param current_user: Current authenticated user.
    :type current_user: User
    :raises HTTPException: 404 if contact not found.
    :return: None (204 No Content).
    :rtype: None
    """
    ok = await repo_contacts.delete_contact(contact_id, current_user, db)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return None
