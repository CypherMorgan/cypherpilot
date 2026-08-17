"""HTML email templates for CypherPilot notifications.

Each template function returns a (subject, html_body, text_body) tuple
ready for the email delivery service.

Design:
- Inline CSS only (no external stylesheets — email clients strip them).
- Clean, professional design matching the CypherPilot brand.
- Responsive tables for email client compatibility.
"""

from __future__ import annotations


def _base_template(title: str, content_html: str) -> str:
    """Wrap content in a standard email layout."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color:#1a1a2e;padding:24px 32px;">
              <span style="color:#e94560;font-family:'Courier New',monospace;font-size:18px;font-weight:bold;">&gt;CypherPilot_</span>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding:32px;">
              <h2 style="margin:0 0 16px;color:#1a1a2e;font-size:20px;font-weight:600;">{title}</h2>
              {content_html}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:16px 32px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;">
                CypherPilot — AI-Powered Quality Engineering Platform<br>
                <a href="https://cyphermorgan.github.io/cypherpilot/" style="color:#6366f1;text-decoration:none;">View Dashboard</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _badge(color: str, text: str) -> str:
    """Render an inline badge."""
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:12px;'
        f'font-size:12px;font-weight:600;color:#fff;background-color:{color};">'
        f"{text}</span>"
    )


def analysis_completed(
    *,
    analysis_type: str,
    title: str,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[str, str, str]:
    """Template for analysis completion emails."""
    subject = f"CypherPilot — {analysis_type} Complete: {title}"

    badge_color = "#22c55e"  # green
    type_label = analysis_type.replace("_", " ").title()

    provider_line = ""
    if provider:
        provider_line = f'<p style="margin:8px 0 0;color:#6b7280;font-size:14px;">Provider: <strong>{provider}</strong>{f" / {model}" if model else ""}</p>'

    content = f"""
      {_badge(badge_color, "Completed")}
      <p style="margin:16px 0 0;color:#374151;font-size:15px;line-height:1.6;">
        Your <strong>{type_label}</strong> analysis has completed successfully.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;background-color:#f8f9fa;border-radius:8px;padding:16px;">
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">Session:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{title}</span>
          </td>
        </tr>
      </table>
      {provider_line}
    """

    text = (
        f"CypherPilot — {type_label} Complete\n\n"
        f"Your {type_label} analysis has completed successfully.\n"
        f"Session: {title}\n"
    )

    return subject, _base_template(f"{type_label} Complete", content), text


def analysis_failed(
    *,
    analysis_type: str,
    title: str,
    error: str | None = None,
) -> tuple[str, str, str]:
    """Template for analysis failure emails."""
    subject = f"CypherPilot — {analysis_type} Failed: {title}"

    badge_color = "#ef4444"  # red
    type_label = analysis_type.replace("_", " ").title()

    error_section = ""
    error_text = ""
    if error:
        truncated = error[:300] + ("..." if len(error) > 300 else "")
        error_section = f"""
      <div style="margin:16px 0;padding:12px;background-color:#fef2f2;border:1px solid #fecaca;border-radius:8px;">
        <p style="margin:0;color:#991b1b;font-size:13px;font-weight:600;">Error Details</p>
        <pre style="margin:8px 0 0;color:#7f1d1d;font-size:12px;font-family:'Courier New',monospace;white-space:pre-wrap;word-break:break-word;">{truncated}</pre>
      </div>"""
        error_text = f"\nError: {truncated}\n"

    content = f"""
      {_badge(badge_color, "Failed")}
      <p style="margin:16px 0 0;color:#374151;font-size:15px;line-height:1.6;">
        Your <strong>{type_label}</strong> analysis has failed.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;background-color:#f8f9fa;border-radius:8px;padding:16px;">
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">Session:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{title}</span>
          </td>
        </tr>
      </table>
      {error_section}
    """

    text = (
        f"CypherPilot — {type_label} Failed\n\n"
        f"Your {type_label} analysis has failed.\n"
        f"Session: {title}\n"
        f"{error_text}"
    )

    return subject, _base_template(f"{type_label} Failed", content), text


def team_invite(
    *,
    team_name: str,
    role: str,
) -> tuple[str, str, str]:
    """Template for team invitation emails."""
    subject = f"CypherPilot — Team Invitation: {team_name}"

    badge_color = "#8b5cf6"  # violet

    content = f"""
      {_badge(badge_color, "Team Invitation")}
      <p style="margin:16px 0 0;color:#374151;font-size:15px;line-height:1.6;">
        You have been invited to join a team on CypherPilot.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;background-color:#f8f9fa;border-radius:8px;padding:16px;">
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">Team:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{team_name}</span>
          </td>
        </tr>
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">Role:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{role}</span>
          </td>
        </tr>
      </table>
    """

    text = (
        f"CypherPilot — Team Invitation\n\n"
        f"You have been invited to join a team on CypherPilot.\n"
        f"Team: {team_name}\n"
        f"Role: {role}\n"
    )

    return subject, _base_template(f"Team Invitation: {team_name}", content), text


def team_removed(
    *,
    team_name: str,
) -> tuple[str, str, str]:
    """Template for team removal emails."""
    subject = f"CypherPilot — Removed from Team: {team_name}"

    badge_color = "#ef4444"  # red

    content = f"""
      {_badge(badge_color, "Removed from Team")}
      <p style="margin:16px 0 0;color:#374151;font-size:15px;line-height:1.6;">
        You have been removed from a team on CypherPilot.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;background-color:#f8f9fa;border-radius:8px;padding:16px;">
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">Team:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{team_name}</span>
          </td>
        </tr>
      </table>
    """

    text = (
        f"CypherPilot — Removed from Team\n\n"
        f"You have been removed from a team on CypherPilot.\n"
        f"Team: {team_name}\n"
    )

    return subject, _base_template(f"Removed from Team: {team_name}", content), text


def team_role_changed(
    *,
    team_name: str,
    role: str,
) -> tuple[str, str, str]:
    """Template for team role change emails."""
    subject = f"CypherPilot — Role Updated: {team_name}"

    badge_color = "#8b5cf6"  # violet

    content = f"""
      {_badge(badge_color, "Role Updated")}
      <p style="margin:16px 0 0;color:#374151;font-size:15px;line-height:1.6;">
        Your role in a team on CypherPilot has been updated.
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;background-color:#f8f9fa;border-radius:8px;padding:16px;">
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">Team:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{team_name}</span>
          </td>
        </tr>
        <tr>
          <td style="padding:4px 0;">
            <span style="color:#6b7280;font-size:13px;">New Role:</span>
            <span style="color:#1a1a2e;font-size:13px;font-weight:500;">{role}</span>
          </td>
        </tr>
      </table>
    """

    text = (
        f"CypherPilot — Role Updated\n\n"
        f"Your role in a team on CypherPilot has been updated.\n"
        f"Team: {team_name}\n"
        f"New Role: {role}\n"
    )

    return subject, _base_template(f"Role Updated: {team_name}", content), text
