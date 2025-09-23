from enum import Enum
from fastapi import Depends, HTTPException, status
from src.services.auth import auth_service
from src.database.models import User


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


class RoleAccess:
    
    """
    Dependency for role-based access control.

    Used in FastAPI routes to restrict access to certain roles.

    Example::

        from fastapi import APIRouter, Depends
        from src.services.permissions import access_admin_only

        router = APIRouter()

        @router.get("/admin", dependencies=[Depends(access_admin_only)])
        async def admin_only_route():
            return {"message": "Admins only"}

    """    

    def __init__(self, allowed: list[Role]):
        
        """
        Initialize with a list of allowed roles.

        :param allowed: List of roles that are permitted.
        :type allowed: list[Role]
        """        
        
        self.allowed = set(allowed)


    async def __call__(
        self, current_user: User = Depends(auth_service.get_current_user)
    ) -> User:
        
        """
        Verify that the current user has one of the allowed roles.

        :param current_user: User object from the current request (resolved via JWT).
        :type current_user: User
        :raises HTTPException: 403 if role not permitted.
        :return: Current user if role is permitted.
        :rtype: User
        """        
        
        if current_user.role not in self.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
            )
        return current_user


#: Dependency that allows only admins.
access_admin_only = RoleAccess([Role.admin])

#: Dependency that allows admins or moderators.
access_admin_or_moderator = RoleAccess([Role.admin, Role.moderator])
