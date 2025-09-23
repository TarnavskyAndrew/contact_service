import uuid


def unique_email(prefix: str) -> str:
    """
    Generate a unique email address for test purposes.

    The function appends a short UUID-based suffix to the given prefix,
    ensuring that each email is unique and avoids duplicate constraint
    errors in the database during repeated test runs.

    :param prefix: Prefix string used to identify the test case.
    :type prefix: str
    :return: Unique email address in the form "<prefix>_<random>@example.com".
    :rtype: str
    """
    return f"{prefix}_{uuid.uuid4().hex[:6]}@example.com"
