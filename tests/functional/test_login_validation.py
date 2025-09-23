import pytest
from tests.utils.login_helpers import load_cases, make_id


# Run with: pytest tests/functional/test_login_validation.py -v

# Load all validation cases from CSV
cases = load_cases("login_cases_validation.csv")


@pytest.mark.login
@pytest.mark.parametrize("case", cases, ids=[make_id(c) for c in cases])
def test_login_validation(client, case):
    """
    Functional tests for /auth/login validation.

    Data source:
        - cases are loaded from login_cases_validation.csv
        - each case has:
            * case_id (optional): unique identifier
            * description (optional): logical description name (e.g., 'email', 'password')
            * email (str): email field value
            * password (str): password field value
            * expected_status (int): expected HTTP status code
            * expected_msg (str): expected message substring

    Validation rules tested:
        - Email format (empty, invalid, special symbols, etc.)
        - Password constraints (empty, too short, too long, etc.)
        - Business logic (valid format but wrong credentials)

    Each case from CSV is converted into a pytest test with a readable ID
    (e.g., "E01-email_empty" or "P03-password_short").
    """
    resp = client.post(
        "/api/auth/login",
        json={
            "email": case["email"],
            "password": case["password"],
        },
    )

    # Assert status code
    assert resp.status_code == case["expected_status"]

    # Assert message (normalize to lowercase for safety)
    msg = resp.text.lower()
    assert case["expected_msg"].lower() in msg
