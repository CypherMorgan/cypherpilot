"""Async email delivery service.

Provides a non-blocking ``send_email`` function that sends emails via
SMTP.  Used by the notification system to deliver email alerts when a
user has email notifications enabled.

Design:
- All sends are fire-and-forget; errors are logged but never raised.
- Uses ``aiosmtplib`` for async SMTP delivery.
- Supports TLS (STARTTLS) and SSL connections.
"""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import aiosmtplib
from structlog import get_logger

if TYPE_CHECKING:
    from app.config import SMTPConfig

_logger = get_logger(__name__)


async def send_email(
    *,
    config: SMTPConfig,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """Send an email via SMTP. Returns True on success, False on failure.

    Errors are logged but never raised — email delivery is best-effort.
    """
    if not config.host:
        _logger.debug("SMTP not configured — skipping email send")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{config.from_name} <{config.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Plain text fallback
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))

        # HTML body (preferred)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Determine connection type
        use_tls = config.use_tls
        use_ssl = config.use_ssl

        if use_ssl:
            await aiosmtplib.send(
                msg,
                hostname=config.host,
                port=config.port,
                username=config.username or None,
                password=config.password or None,
                use_tls=True,
                timeout=config.timeout_seconds,
            )
        elif use_tls:
            await aiosmtplib.send(
                msg,
                hostname=config.host,
                port=config.port,
                username=config.username or None,
                password=config.password or None,
                start_tls=True,
                timeout=config.timeout_seconds,
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=config.host,
                port=config.port,
                username=config.username or None,
                password=config.password or None,
                timeout=config.timeout_seconds,
            )

        _logger.info(
            "Email sent successfully",
            to=to_email,
            subject=subject,
        )
        return True

    except aiosmtplib.SMTPException as exc:
        _logger.error(
            "SMTP error sending email",
            to=to_email,
            subject=subject,
            error=str(exc),
        )
        return False
    except OSError as exc:
        _logger.error(
            "Network error sending email",
            to=to_email,
            subject=subject,
            error=str(exc),
        )
        return False
    except Exception as exc:
        _logger.error(
            "Unexpected error sending email",
            to=to_email,
            subject=subject,
            error=str(exc),
        )
        return False
