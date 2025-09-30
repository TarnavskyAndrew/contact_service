from enum import Enum


class Role(str, Enum):
    """
    Enumeration of user roles.

    - ``admin`` : Full access.
    - ``moderator`` : Limited management access.
    - ``user`` : Regular user.
    """

    admin = "admin"
    moderator = "moderator"
    user = "user"
