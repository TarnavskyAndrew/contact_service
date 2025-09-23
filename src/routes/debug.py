from fastapi import APIRouter, Request, Depends
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
import inspect

from src.database.db import get_db
from src.services.email import send_email
from src.schemas import DebugEmailRequest


router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/send")
async def debug_send(
    body: DebugEmailRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):    
    """
    Debug endpoint: send a test email.

    - Always uses the ``debug`` username.
    - Sends an email with a link pointing to ``/debug/ok``.

    :param body: Email request payload (recipient).
    :type body: DebugEmailRequest
    :param request: Current request (to construct base URL).
    :type request: Request
    :param db: Active database session (not used directly).
    :type db: AsyncSession
    :return: JSON with status flag.
    :rtype: dict

    Example response::

        {
            "ok": true
        }
    """    
    
    link = f"{str(request.base_url)}debug/ok"
    await send_email(
        email=body.email,
        username="debug",
        link=link,
        template_name="email_template.html",
    )
    return {"ok": True}


@router.get("/__routes")
async def debug_routes(request: Request):

    """
    Debug endpoint: list all application routes.

    Iterates over registered FastAPI routes and returns:
    - Path
    - Methods
    - Endpoint function (module + name)
    - Source file and line (if available)
    - Tags and summary

    :param request: Current request (used to access app context).
    :type request: Request
    :return: Dictionary with route metadata.
    :rtype: dict

    Example response::

        {
            "routes": [
                {
                    "path": "/api/auth/login",
                    "methods": ["POST"],
                    "endpoint": "src.routes.auth.login",
                    "file": "src/routes/auth.py",
                    "line": 42,
                    "tags": ["auth"],
                    "summary": null
                },
                ...
            ]
        }
    """    
    
    app = request.app
    items = []

    for r in app.routes:
        if isinstance(r, APIRoute):
            fn = r.endpoint
            try:
                file = inspect.getsourcefile(fn)
                line = inspect.getsourcelines(fn)[1] if file else None
            except (OSError, TypeError):
                file, line = None, None

            items.append(
                {
                    "path": r.path,
                    "methods": sorted(list(r.methods)),
                    "endpoint": f"{fn.__module__}.{fn.__name__}",
                    "file": file,
                    "line": line,
                    "tags": r.tags,
                    "summary": r.summary,
                }
            )

    return {"routes": items}
