import pytest
import uuid
from tests.utils.auth_helpers import extract_error


# Run with: pytest tests/functional/test_signup_validation.py -v

"""
Validation cases for /auth/signup (UserModel):

- username: min_length=2, max_length=32
- email: EmailStr (RFC-friendly regex, ASCII only)
- password: min_length=6, max_length=64

Notes:
- All invalid payloads → 422 Validation failed
- All valid payloads → 201 User created
"""

signup_cases = [
    # --- USERNAME ---
    {
        "id": "U01-username_empty",
        "username": "",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "U02-username_too_short",
        "username": "A",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "U03-username_min_length",
        "username": "AB",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U04-username_max_length",
        "username": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U05-username_too_long",
        "username": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "U06-username_starts_underscore",
        "username": "_user",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U07-username_starts_dot",
        "username": ".user",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U08-username_starts_dash",
        "username": "-user",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U09-username_starts_comma",
        "username": ",user",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U10-username_unicode",
        "username": "имя",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "U11-username_chinese",
        "username": "名字",
        "email": "ok@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    # --- EMAIL ---
    {
        "id": "E01-email_empty",
        "username": "ok",
        "email": "",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E02-email_no_at",
        "username": "ok",
        "email": "invalid-email",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E03-email_double_at",
        "username": "ok",
        "email": "user@@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E04-email_space_before",
        "username": "ok",
        "email": "user @example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E05-email_space_after",
        "username": "ok",
        "email": "user@ example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E06-email_spaces_around",
        "username": "ok",
        "email": " other@example.com ",  # in real use -> valid in schema - strip()
        "password": "Secret123",
        "status": 201,
        "msg": "Created",
    },
    {
        "id": "E07-email_starts_dot",
        "username": "ok",
        "email": ".user@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E08-email_starts_dash",
        "username": "ok",
        "email": "-user@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E09-email_starts_comma",
        "username": "ok",
        "email": ",user@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E10-email_ends_dot",
        "username": "ok",
        "email": "user.@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E11-email_with_dollar",
        "username": "ok",
        "email": "user$name@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E12-email_with_brackets",
        "username": "ok",
        "email": "user<>@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E13-email_with_comma",
        "username": "ok",
        "email": "user,comma@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E14-email_too_long",
        "username": "ok",
        "email": "averylong.......................................................................................................................................................................................................................................................@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E15-email_domain_no_dot",
        "username": "ok",
        "email": "user@example",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E16-email_unicode",
        "username": "ok",
        "email": "юзер@пример.рф",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E17-email_double_dot_local",
        "username": "ok",
        "email": "user..name@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E18-email_double_dot_domain",
        "username": "ok",
        "email": "user@example..com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E19-email_domain_starts_dash",
        "username": "ok",
        "email": "user@-example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E20-email_domain_ends_dash",
        "username": "ok",
        "email": "user@example-.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E21-email_domain_with_underscore",
        "username": "ok",
        "email": "user@exam_ple.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E22-email_local_too_long",
        "username": "ok",
        "email": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E23-email_total_too_long",
        "username": "ok",
        "email": "averylong.................................................................................................................................................................................................................................................................@example.com",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E24-email_too_short",
        "username": "ok",
        "email": "a@b.c",
        "password": "Secret123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "E25-email_min_length",
        "username": "ok",
        "email": "a@b.co",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    # --- PASSWORD ---
    {
        "id": "P01-password_empty",
        "username": "ok",
        "email": "user@example.com",
        "password": "",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "P02-password_short",
        "username": "ok",
        "email": "user@example.com",
        "password": "123",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "P03-password_spaces",
        "username": "ok",
        "email": "user@example.com",
        "password": "     ",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "P04-password_too_long",
        "username": "ok",
        "email": "user@example.com",
        "password": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "status": 422,
        "msg": "validation failed",
    },
    {
        "id": "P05-password_only_spaces",
        "username": "ok",
        "email": "user@example.com",
        "password": "        ",
        "status": 422,
        "msg": "validation failed",
    },
    # {
    #     "id": "P06-password_common_word",  # TODO: Password strength check implemented, not running
    #     "username": "ok",
    #     "email": "user@example.com",
    #     "password": "password",
    #     "status": 422,
    #     "msg": "validation failed",
    # },
    # --- POSITIVE CASES ---
    {
        "id": "V01-valid_minimal",
        "username": "ok",
        "email": "user@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "V02-valid_with_dot_in_local",
        "username": "ok",
        "email": "user.name@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "V03-valid_with_dash_in_local",
        "username": "ok",
        "email": "user-name@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "V04-valid_with_underscore_in_local",
        "username": "ok",
        "email": "user_name@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
    {
        "id": "V05-valid_with_plus_tag",
        "username": "ok",
        "email": "user+tag@example.com",
        "password": "Secret123",
        "status": 201,
        "msg": "User created",
    },
]


@pytest.mark.signup
@pytest.mark.parametrize("case", signup_cases, ids=[c["id"] for c in signup_cases])
def test_signup_validation(client, case):
    """
    Parametrized signup validation test.

    Each case provides:
    - unique id (for pytest reporting)
    - username
    - email
    - password
    - expected HTTP status
    - expected message substring
    """
    # Ensure unique email for "201" cases → avoid 409 conflict
    email = case["email"]
    if case["status"] == 201:
        local, domain = email.split("@")
        email = f"{local}+{uuid.uuid4().hex[:6]}@{domain}"

    resp = client.post(
        "/api/auth/signup",
        json={
            "username": case["username"],
            "email": email,
            "password": case["password"],
        },
    )
    assert (
        resp.status_code == case["status"]
    ), f"{case['id']} failed with {resp.status_code}"
    msg = (
        extract_error(resp.json()).lower()
        if resp.status_code != 201
        else resp.json()["detail"].lower()
    )
    assert case["msg"].lower() in msg
