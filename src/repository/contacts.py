from datetime import date, timedelta
from typing import List
from sqlalchemy import select, or_, and_, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate


async def get_contacts(
    skip: int, limit: int, user: User, db: AsyncSession
) -> List[Contact]:
    """
    Retrieve a paginated list of contacts for the given user,
    sorted by ID in ascending order.

    :param skip: Number of records to skip (offset).
    :type skip: int
    :param limit: Maximum number of records to return.
    :type limit: int
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: List of contacts.
    :rtype: list[Contact]
    """

    result = await db.execute(
        select(Contact)
        .where(Contact.user_id == user.id)
        .order_by(Contact.id)  # sorting by ID
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_contact(contact_id: int, user: User, db: AsyncSession) -> Contact | None:
    """
    Retrieve a single contact by ID for the given user.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: Contact object if found, else None.
    :rtype: Contact | None
    """
    result = await db.execute(
        select(Contact).where(
            and_(Contact.id == contact_id, Contact.user_id == user.id)
        )
    )
    return result.scalar_one_or_none()


async def create_contact(body: ContactCreate, user: User, db: AsyncSession) -> Contact:
    """
    Create a new contact for the given user.

    :param body: Contact creation payload.
    :type body: ContactCreate
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :raises HTTPException: 409 Conflict if email already exists.
    :return: Newly created contact.
    :rtype: Contact
    """

    contact = Contact(**body.model_dump(), user_id=user.id)
    db.add(contact)
    try:
        await db.commit()
        await db.refresh(contact)
        return contact
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )


async def update_contact(
    contact_id: int, body: ContactUpdate, user: User, db: AsyncSession
) -> Contact | None:
    """
    Update an existing contact for the given user.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param body: Contact update payload.
    :type body: ContactUpdate
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: Updated contact if found, else None.
    :rtype: Contact | None
    """

    result = await db.execute(
        select(Contact).where(
            and_(Contact.id == contact_id, Contact.user_id == user.id)
        )
    )
    contact = result.scalar_one_or_none()
    if contact:
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, field, value)
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, user: User, db: AsyncSession) -> bool:
    """
    Delete a contact by ID for the given user.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: True if contact was deleted, False otherwise.
    :rtype: bool
    """

    result = await db.execute(
        select(Contact).where(
            and_(Contact.id == contact_id, Contact.user_id == user.id)
        )
    )
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    if not contact:
        return False
    return True
    # return contact #_______________________змінив для тестів


async def search_contacts(q: str, user: User, db: AsyncSession) -> List[Contact]:
    """
    Search contacts by first name, last name, or email.

    :param q: Search query (substring).
    :type q: str
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: List of contacts matching the query.
    :rtype: list[Contact]
    """

    like = f"%{q}%"
    res = await db.execute(
        select(Contact).where(
            and_(
                Contact.user_id == user.id,
                or_(
                    Contact.first_name.ilike(like),
                    Contact.last_name.ilike(like),
                    Contact.email.ilike(like),
                ),
            )
        )
    )
    return list(res.scalars().all())


# async def get_upcoming_birthdays(days: int, user: User, db: AsyncSession) -> List[Contact]:

#     """
#     Get contacts with birthdays in the next N days.

#     Handles year wrap-around (e.g., December → January).

#     :param days: Number of days ahead to check.
#     :type days: int
#     :param user: The current authenticated user.
#     :type user: User
#     :param db: Active database session.
#     :type db: AsyncSession
#     :return: List of contacts with upcoming birthdays.
#     :rtype: list[Contact]
#     """

#     today = date.today()
#     end_date = today + timedelta(days=days)

#     today_md = today.strftime("%m-%d")
#     end_md = end_date.strftime("%m-%d")

#     if today_md <= end_md:
#         # without going through the New Year
#         stmt = select(Contact).where(
#             and_(
#                 Contact.user_id == user.id,
#                 func.to_char(Contact.birthday, "MM-DD").between(today_md, end_md),
#             )
#         )
#     else:
#         # with the transition over the New Year (for example, 28.12 → 05.01)
#         stmt = select(Contact).where(
#             and_(
#                 Contact.user_id == user.id,
#                 or_(
#                     func.to_char(Contact.birthday, "MM-DD") >= today_md,
#                     func.to_char(Contact.birthday, "MM-DD") <= end_md,
#                 ),
#             )
#         )

#     res = await db.execute(stmt)
#     return list(res.scalars().all())


async def get_upcoming_birthdays(
    days: int, user: User, db: AsyncSession
) -> List[Contact]:
    """
    Get contacts with birthdays in the next N days.

    Handles year wrap-around (e.g., December → January).

    This function is database-agnostic:
      - For PostgreSQL it uses `to_char(Contact.birthday, 'MM-DD')`
      - For SQLite (used in tests) it uses `strftime('%m-%d', Contact.birthday)`

    :param days: Number of days ahead to check.
    :type days: int
    :param user: The current authenticated user.
    :type user: User
    :param db: Active database session.
    :type db: AsyncSession
    :return: List of contacts with upcoming birthdays.
    :rtype: list[Contact]
    """

    today = date.today()
    end_date = today + timedelta(days=days)

    today_md = today.strftime("%m-%d")
    end_md = end_date.strftime("%m-%d")

    # We select a function for the DB, for tests
    if db.bind.dialect.name == "sqlite":
        birthday_expr = func.strftime("%m-%d", Contact.birthday)
    else:
        birthday_expr = func.to_char(Contact.birthday, "MM-DD")

    if today_md <= end_md:
        # without going through the New Year
        stmt = select(Contact).where(
            and_(
                Contact.user_id == user.id,
                birthday_expr.between(today_md, end_md),
            )
        )
    else:
        # with the transition over the New Year (for example, 28.12 → 05.01)
        stmt = select(Contact).where(
            and_(
                Contact.user_id == user.id,
                or_(
                    birthday_expr >= today_md,
                    birthday_expr <= end_md,
                ),
            )
        )

    # Add sorting by month and day (ignoring year)
    stmt = stmt.order_by(
        extract("month", Contact.birthday),
        extract("day", Contact.birthday),
    )

    res = await db.execute(stmt)
    return list(res.scalars().all())
