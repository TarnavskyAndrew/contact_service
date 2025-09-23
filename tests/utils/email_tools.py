from typing import List


# from tests.utils.email_tools import check_email_length, get_email_length, bulk_email_length

"""
Utility functions for working with email test cases.

Includes helpers to measure total length, local-part length,
and domain length of one or more email strings.


# One email
check_email_length("aaaaaaa@sss.com")

# Constr. email
domain = "d" * 185
local = "a" * 64
email = f"{local}@{domain}.com"
check_email_length(email)

# Multi email
emails = ["user@example.com", "user..name@example.com", email]
bulk_info = bulk_email_length(emails)
for info in bulk_info:
    print(info)

"""

def check_email_length(*emails: str) -> None:
    """
    Print length details for one or more email strings.

    :param emails: One or more email strings to check.
    :type emails: str
    :return: None (prints details to console)
    """
    for email in emails:
        local, _, domain = email.partition("@")
        total_len = len(email)
        print(f"\nEmail: {email}")
        print(f"  Total length: {total_len}")
        print(f"  Local-part length: {len(local)}")
        print(f"  Domain length: {len(domain)}")


def get_email_length(email: str) -> dict:
    """
    Return length details for a single email as a dict.

    :param email: Email string to check.
    :type email: str
    :return: Dictionary with total, local, and domain lengths.
    :rtype: dict
    """
    local, _, domain = email.partition("@")
    return {
        "email": email,
        "total": len(email),
        "local": len(local),
        "domain": len(domain),
    }


def bulk_email_length(emails: List[str]) -> List[dict]:
    """
    Return length details for multiple emails.

    :param emails: List of email strings to check.
    :type emails: List[str]
    :return: List of dicts with length details.
    :rtype: List[dict]
    """
    return [get_email_length(e) for e in emails]


# check_email_length("aaaaaaa@sss.com")

local = "a" * 64
domain = "b" * 63 + "." + "c" * 50 + "." + "d" * 50 # 169
email = f"{local}@{domain}.com"
check_email_length(email)

