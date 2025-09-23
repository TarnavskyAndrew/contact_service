import pytest
import pytest_asyncio
from datetime import date

from src.repository import contacts
from src.schemas import ContactCreate, ContactUpdate
from src.database.models import User, Contact


# Run with: pytest tests/unit/test_repository_contacts.py -v

@pytest_asyncio.fixture
async def test_user(db_session):
    """
    Create a test user directly in the DB.

    :param db_session: Async DB session
    :return: Persisted user instance
    :rtype: User
    """
    user = User(username="owner", email="owner@example.com", password="pwd")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ----------------------------------------------------------------------
# CRUD Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(db_session, test_user):
    """Repository should create a new contact and assign it to the user."""
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="123456789",
        birthday=date(1990, 1, 1),
        extra="friend",
    )
    contact = await contacts.create_contact(contact_data, test_user, db_session)
    assert contact.email == "john@example.com"
    assert contact.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_contacts(db_session, test_user):
    """Repository should return a list of user's contacts."""
    c = Contact(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        phone="111",
        birthday=date(1995, 5, 5),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()

    result = await contacts.get_contacts(0, 10, test_user, db_session)
    assert any(r.email == "alice@example.com" for r in result)


@pytest.mark.asyncio
async def test_get_contact_found_and_not_found(db_session, test_user):
    """Repository should return contact if found, None if not."""
    c = Contact(
        first_name="Kate",
        last_name="Snow",
        email="kate@example.com",
        phone="222",
        birthday=date(2000, 2, 2),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    found = await contacts.get_contact(c.id, test_user, db_session)
    assert found.email == "kate@example.com"

    not_found = await contacts.get_contact(999, test_user, db_session)
    assert not_found is None


@pytest.mark.asyncio
async def test_update_contact_success(db_session, test_user):
    """Repository should update existing contact fields."""
    c = Contact(
        first_name="Bob",
        last_name="Marley",
        email="bob@example.com",
        phone="333",
        birthday=date(1999, 3, 3),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    body = ContactUpdate(
        first_name="Bobby",
        last_name="Marley",
        email="bob@example.com",
        phone="999",
        birthday=date(1999, 3, 3),
        extra="musician",
    )
    updated = await contacts.update_contact(c.id, body, test_user, db_session)
    assert updated.first_name == "Bobby"
    assert updated.phone == "999"


@pytest.mark.asyncio
async def test_update_contact_not_found(db_session, test_user):
    """Repository should return None when trying to update a non-existent contact."""
    body = ContactUpdate(
        first_name="Ghost",
        last_name="None",
        email="ghost@example.com",
        phone="000",
        birthday=date(1991, 1, 1),
        extra=None,
    )
    result = await contacts.update_contact(999, body, test_user, db_session)
    assert result is None


@pytest.mark.asyncio
async def test_delete_contact_found_and_not_found(db_session, test_user):
    """Repository should delete existing contact, return False if not found."""
    c = Contact(
        first_name="Tom",
        last_name="Jerry",
        email="tom@example.com",
        phone="444",
        birthday=date(1998, 4, 4),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    ok = await contacts.delete_contact(c.id, test_user, db_session)
    assert ok

    not_found = await contacts.delete_contact(999, test_user, db_session)
    assert not_found is False


@pytest.mark.asyncio
async def test_search_contacts(db_session, test_user):
    """Repository should find contacts by substring in first/last name or email."""
    c = Contact(
        first_name="Search",
        last_name="Target",
        email="target@example.com",
        phone="555",
        birthday=date(1997, 7, 7),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()

    result = await contacts.search_contacts("target", test_user, db_session)
    assert len(result) >= 1
    assert result[0].email == "target@example.com"


# ----------------------------------------------------------------------
# Upcoming Birthdays Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_upcoming_birthdays_no_year_wrap(db_session, test_user):
    """Repository should return contacts with birthdays in range (no year wrap)."""
    today = date.today()
    c = Contact(
        first_name="Soon",
        last_name="BDay",
        email="soon@example.com",
        phone="666",
        birthday=date(today.year, today.month, today.day + 3),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()

    result = await contacts.get_upcoming_birthdays(7, test_user, db_session)
    assert any(r.email == "soon@example.com" for r in result)


@pytest.mark.asyncio
async def test_get_upcoming_birthdays_with_year_wrap(
    db_session, test_user, monkeypatch
):
    """Repository should handle year wrap (e.g., Dec → Jan birthdays)."""
    fake_today = date(2025, 12, 28)

    class FakeDate(date):
        @classmethod
        def today(cls):
            return fake_today

    # patch date in repository
    monkeypatch.setattr("src.repository.contacts.date", FakeDate)

    c = Contact(
        first_name="NewYear",
        last_name="Baby",
        email="ny@example.com",
        phone="777",
        birthday=date(2026, 1, 3),
        user_id=test_user.id,
    )
    db_session.add(c)
    await db_session.commit()

    result = await contacts.get_upcoming_birthdays(10, test_user, db_session)
    assert any(r.email == "ny@example.com" for r in result)
