Deployment
==========

This section describes how to run the Contacts API project locally
and in production using Docker Compose.

Environment Variables
---------------------

The application requires environment variables, provided via ``.env`` file.
See ``.env.example`` in the project root for reference.

Key variables:

- **DATABASE_URL** – full DB URL (async).
- **SECRET_KEY** – JWT secret key.
- **MAIL_USERNAME / MAIL_PASSWORD / MAIL_SERVER / MAIL_PORT** – SMTP credentials.
- **CLOUDINARY_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET** – Cloudinary.
- **REDIS_HOST / REDIS_PORT** – Redis configuration.

Example ``.env``::

    DATABASE_URL=postgresql+asyncpg://user:password@db:5432/contacts_db
    SECRET_KEY=supersecretkey
    MAIL_USERNAME=test@example.com
    MAIL_PASSWORD=secret
    MAIL_SERVER=smtp.mailtrap.io
    MAIL_PORT=2525
    CLOUDINARY_NAME=myapp
    CLOUDINARY_API_KEY=123456789
    CLOUDINARY_API_SECRET=abcdef123456
    REDIS_HOST=redis
    REDIS_PORT=6379

Docker Compose
--------------

To start the application stack (Postgres, Redis, API):

.. code-block:: bash

    docker-compose up --build

This will start:

- **contacts-api** (FastAPI app, served via uvicorn)
- **db** (PostgreSQL database)
- **redis** (Redis cache)
- **pgadmin** (database administration UI)

Then open http://localhost:8000/docs for Swagger UI.
