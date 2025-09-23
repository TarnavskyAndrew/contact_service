import time
from fastapi import Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware


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


def setup_middlewares(app):
    
    """
    Register middlewares for the FastAPI application.

    - Adds custom middleware :func:`add_process_time_header`.
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

    # register CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # or restrict to ["http://localhost:3000"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
