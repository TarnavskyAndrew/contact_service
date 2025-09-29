import time
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware


MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


async def add_process_time_header(request: Request, call_next):
    """
    Middleware: measure and add request processing time.

    - Records the start time before passing request to the next handler.
    - After processing, calculates elapsed time.
    - Adds custom header ``X-Process-Time`` with processing time in seconds.

    :param request: Incoming FastAPI request.
    :type request: Request
    :param call_next: Next request handler in the middleware chain.
    :type call_next: Callable
    :return: Response with an additional header.
    :rtype: Response

    Example header::

        X-Process-Time: 0.003512
    """

    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)  # add to headers
    return response


async def limit_upload_size(request: Request, call_next):
    """
    Middleware: enforce file upload size limit for avatar endpoints.

    - Applies only to ``PUT /users/avatar`` and ``PATCH /users/avatar``.
    - Checks ``Content-Length`` header before reading body.
    - Rejects requests larger than 2 MB with HTTP 413.

    :param request: Incoming FastAPI request.
    :type request: Request
    :param call_next: Next request handler in the middleware chain.
    :type call_next: Callable
    :return: Response or HTTP 413 exception if payload too large.
    :rtype: Response
    """
    if request.url.path.endswith("/avatar") and request.method in ("PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024 * 1024)}MB",
            )
    return await call_next(request)


def setup_middlewares(app):
    """
    Register middlewares for the FastAPI application.

    - Adds :func:`add_process_time_header` to measure processing time.
    - Adds :func:`limit_upload_size` to restrict avatar upload size to 2MB.
    - Configures **CORS** with permissive settings (all origins, all methods).

    :param app: FastAPI application instance.
    :type app: FastAPI
    :return: None
    :rtype: None

    Example::

        from fastapi import FastAPI
        from src.middleware import setup_middlewares

        app = FastAPI()
        setup_middlewares(app)
    """

    # register custom middleware
    app.middleware("http")(add_process_time_header)  # add new middleware here ->
    app.middleware("http")(limit_upload_size)  # new size limit

    # register CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # or restrict to ["http://localhost:3000"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
