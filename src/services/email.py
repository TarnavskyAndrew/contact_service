import os
import logging
from pathlib import Path
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from src.conf.config import settings


logger = logging.getLogger(__name__)

#: Directory for storing emails locally if SMTP is unavailable or DEBUG mode enabled.
TMP_EMAIL_DIR = Path(__file__).resolve().parent.parent / "tmp_emails"
TMP_EMAIL_DIR.mkdir(exist_ok=True)


#: Global mail configuration (FastAPI-Mail).
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="Contacts API",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).resolve().parent / "templates",
)


async def send_email(
    email: EmailStr,
    username: str,
    link: str,
    template_name: str = "email_template.html",
):
    """
    Send an email with optional fallback to local file.

    :param email: Recipient email address.
    :type email: EmailStr
    :param username: Recipient username (used in template).
    :type username: str
    :param link: Link to include in the email.
    :type link: str
    :param template_name: HTML template file (default = ``email_template.html``).
    :type template_name: str, optional
    :return: None
    :rtype: None

    Example::

        await send_email(
            email="user@example.com",
            username="John",
            link="http://localhost:8000/api/auth/confirm/abc123",
        )
    """

    subject = (
        "Confirm your email" if "reset" not in template_name else "Reset your password"
    )

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        template_body={
            "username": username,
            "link": link,
            "token": link.split("/")[-1],
        },
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message, template_name=template_name)
        logger.info(f"Email sent to {email} ({template_name})")

    except ConnectionErrors as err:
        logger.error(f"Email sending failed: {err}")

    if settings.DEBUG_EMAILS:  # Save only if DEBUG_EMAILS=True
        filename = (
            TMP_EMAIL_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{email}.html"
        )
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<h2>{subject}</h2><p>Hello {username},</p>")
            f.write(f"<p>Use this link: <a href='{link}'>{link}</a></p>")
        logger.info(f"Email saved to {filename}")
