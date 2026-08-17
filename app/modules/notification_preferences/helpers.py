"""Email notification helper for the notification system.

Provides a non-blocking ``send_notification_email`` function that checks
user preferences and sends an email if the event type is enabled.

Design:
- Called after a notification is created in the database.
- Checks notification_preferences to decide whether to send.
- Email delivery is fire-and-forget; errors are swallowed.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.email import send_email
from app.infrastructure.email_templates import (
    analysis_completed,
    analysis_failed,
    team_invite,
    team_removed,
    team_role_changed,
)
from app.modules.auth.models import User
from app.modules.notification_preferences.repository import (
    NotificationPreferenceRepository,
)

_logger = get_logger(__name__)


async def send_notification_email(
    db: AsyncSession,
    *,
    user_id: Any,
    type_: str,
    title: str,
    message: str,  # noqa: ARG001 — kept for interface consistency with create_notification
    resource_type: str | None = None,  # noqa: ARG001
    resource_id: Any = None,  # noqa: ARG001
    extra: dict[str, Any] | None = None,
) -> None:
    """Send an email notification if the user has the event type enabled.

    Non-blocking — errors are swallowed.  Requires SMTP to be configured
    in the application settings.

    Args:
        db: Database session.
        user_id: Target user UUID.
        type_: Event type (e.g. "analysis.completed").
        title: Notification title.
        message: Notification message text.
        resource_type: Optional resource type for context.
        resource_id: Optional resource ID for context.
        extra: Optional dict with additional template context
               (e.g. provider, model, error, team_name, role).
    """
    try:
        from app.config import AppConfig

        config = AppConfig()
        smtp_config = config.smtp

        # Skip if SMTP is not configured
        if not smtp_config.host:
            return

        # Check user preferences
        pref_repo = NotificationPreferenceRepository(db)
        should_send = await pref_repo.should_send_email(user_id, type_)

        if not should_send:
            return

        # Get user email
        user_result = await db.execute(
            select(User).where(User.id == user_id),
        )
        user = user_result.scalar_one_or_none()

        if user is None or not user.email:
            return

        # Build email based on event type
        extra = extra or {}
        subject = ""
        html_body = ""
        text_body = ""

        if type_ == "analysis.completed":
            subject, html_body, text_body = analysis_completed(
                analysis_type=extra.get("analysis_type", "analysis"),
                title=title,
                provider=extra.get("provider"),
                model=extra.get("model"),
            )
        elif type_ == "analysis.failed":
            subject, html_body, text_body = analysis_failed(
                analysis_type=extra.get("analysis_type", "analysis"),
                title=title,
                error=extra.get("error"),
            )
        elif type_ == "team.invite":
            subject, html_body, text_body = team_invite(
                team_name=extra.get("team_name", "Unknown Team"),
                role=extra.get("role", "member"),
            )
        elif type_ == "team.removed":
            subject, html_body, text_body = team_removed(
                team_name=extra.get("team_name", "Unknown Team"),
            )
        elif type_ == "team.role_changed":
            subject, html_body, text_body = team_role_changed(
                team_name=extra.get("team_name", "Unknown Team"),
                role=extra.get("role", "member"),
            )
        else:
            # Unknown event type — skip email
            return

        await send_email(
            config=smtp_config,
            to_email=user.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    except Exception:
        # Email delivery is best-effort — never fail the main request
        pass
