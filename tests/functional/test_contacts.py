import pytest
import copy
import uuid
from datetime import date, timedelta
from sqlalchemy import select

from src.database.models import User, Contact
from tests.utils.auth_helpers import extract_error

# Run with: pytest tests/functional/test_contacts.py -v


@pytest.fixture
async def auth_headers(client, db_session, user):
    """
    Register and confirm a user, then return Authorization header.

    :return: Headers with valid access token.
    :rtype: dict
    """
    # signup
    client.post("/api/auth/signup", json=user)

    # confirm email manually
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    # login
    resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.json()
    tokens = resp.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def make_unique_contact(contact_payload: dict) -> dict:
    """
    Create a copy of contact_payload with a unique email and phone number.

    :param contact_payload: Base contact data.
    :type contact_payload: dict
    :return: Modified contact with unique email/phone.
    :rtype: dict
    """
    data = copy.deepcopy(contact_payload)
    uid = uuid.uuid4().hex[:6]
    data["email"] = f"{uid}@example.com"
    data["phone"] = f"555{uid}"
    return data


@pytest.mark.asyncio
async def test_create_contact(client, auth_headers, contact_payload):
    """User can create a new contact."""
    data = make_unique_contact(contact_payload)
    resp = client.post("/api/contacts/", headers=auth_headers, json=data)
    assert resp.status_code == 201
    result = resp.json()
    assert result["email"] == data["email"]
    assert "id" in result


@pytest.mark.asyncio
async def test_get_contacts(client, auth_headers, contact_payload):
    """User can retrieve the list of their contacts."""
    data = make_unique_contact(contact_payload)
    client.post("/api/contacts/", headers=auth_headers, json=data)

    resp = client.get("/api/contacts/", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert any(c["email"] == data["email"] for c in results)


@pytest.mark.asyncio
async def test_get_contact_found_and_not_found(client, auth_headers, contact_payload):
    """Get contact by ID works; non-existing ID returns 404."""
    data = make_unique_contact(contact_payload)
    resp = client.post("/api/contacts/", headers=auth_headers, json=data)
    contact_id = resp.json()["id"]

    # found
    resp_get = client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["email"] == data["email"]

    # not found
    resp_404 = client.get("/api/contacts/999999", headers=auth_headers)
    assert resp_404.status_code == 404
    msg = extract_error(resp_404.json())
    assert "not found" in msg.lower()


@pytest.mark.asyncio
async def test_update_contact(client, auth_headers, contact_payload):
    """User can update their existing contact."""
    # create contact
    data = make_unique_contact(contact_payload)
    resp = client.post("/api/contacts/", headers=auth_headers, json=data)
    contact_id = resp.json()["id"]

    # update fields
    updated = copy.deepcopy(data)
    updated["first_name"] = "Johnny"
    updated["phone"] = "999888777"

    resp_update = client.put(
        f"/api/contacts/{contact_id}", headers=auth_headers, json=updated
    )
    assert resp_update.status_code == 200
    result = resp_update.json()
    assert result["first_name"] == "Johnny"
    assert result["phone"] == "999888777"


@pytest.mark.asyncio
async def test_delete_contact(client, auth_headers, contact_payload):
    """User can delete their contact; repeat deletion fails with 404."""
    data = make_unique_contact(contact_payload)
    resp = client.post("/api/contacts/", headers=auth_headers, json=data)
    contact_id = resp.json()["id"]

    # delete once
    del_resp = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # delete again → not found
    del_resp2 = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert del_resp2.status_code == 404
    msg = extract_error(del_resp2.json())
    assert "not found" in msg.lower()


@pytest.mark.asyncio
async def test_search_contacts(client, auth_headers, contact_payload):
    """User can search contacts by first name/last name/email."""
    data = make_unique_contact(contact_payload)
    client.post("/api/contacts/", headers=auth_headers, json=data)

    resp = client.get(
        f"/api/contacts/search?q={data['first_name']}", headers=auth_headers
    )
    assert resp.status_code == 200
    results = resp.json()
    assert any(c["email"] == data["email"] for c in results)


@pytest.mark.asyncio
async def test_upcoming_birthdays(client, auth_headers, db_session, contact_payload):
    """Upcoming birthdays endpoint returns contacts with birthdays within N days."""
    result = await db_session.execute(select(User))
    user = result.scalar_one()

    uid = uuid.uuid4().hex[:6]
    contact = Contact(
        first_name="Kate",
        last_name="BDay",
        email=f"kate{uid}@example.com",
        phone=f"444{uid}",
        birthday=date.today() + timedelta(days=3),
        user_id=user.id,
    )
    db_session.add(contact)
    await db_session.commit()

    resp = client.get("/api/contacts/upcoming-birthdays?days=7", headers=auth_headers)
    assert resp.status_code == 200
    emails = [c["email"] for c in resp.json()]
    assert contact.email in emails


# --- Security tests ---


@pytest.mark.asyncio
async def test_contacts_requires_auth(client):
    """Access to contacts without authentication should fail."""
    resp = client.get("/api/contacts/")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_contacts_with_other_user_token(
    client, db_session, user, contact_payload
):
    """
    Ensure user cannot access contacts created under another account.
    """
    # user A
    client.post("/api/auth/signup", json=user)
    result = await db_session.execute(select(User).where(User.email == user["email"]))
    db_user: User = result.scalar_one()
    db_user.confirmed = True
    await db_session.commit()

    login_resp = client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert login_resp.status_code == 200, login_resp.json()
    tokens_a = login_resp.json()
    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    # user B
    other = {"username": "other", "email": "other@example.com", "password": "Secret123"}
    client.post("/api/auth/signup", json=other)
    result2 = await db_session.execute(select(User).where(User.email == other["email"]))
    db_user2: User = result2.scalar_one()
    db_user2.confirmed = True
    await db_session.commit()

    login_resp2 = client.post(
        "/api/auth/login",
        json={"email": other["email"], "password": other["password"]},
    )
    assert login_resp2.status_code == 200, login_resp2.json()
    tokens_b = login_resp2.json()
    headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}

    # user A creates a contact
    data = make_unique_contact(contact_payload)
    resp_create = client.post("/api/contacts/", headers=headers_a, json=data)
    contact_id = resp_create.json()["id"]

    # user B tries to access user A's contact
    resp_forbidden = client.get(f"/api/contacts/{contact_id}", headers=headers_b)
    assert resp_forbidden.status_code in (403, 404)
