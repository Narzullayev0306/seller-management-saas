"""Email delivery with graceful fallback.

When SMTP is not configured (local dev / tests), emails are logged to the
console instead of being sent, so all auth flows keep working end-to-end.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
    <div style="max-width:520px;margin:24px auto;background:#ffffff;border-radius:12px;
                overflow:hidden;border:1px solid #e2e8f0;">
      <div style="background:linear-gradient(135deg,#4f46e5,#38bdf8);padding:20px 24px;">
        <span style="color:#ffffff;font-size:18px;font-weight:bold;">Seller Manager</span>
      </div>
      <div style="padding:24px;">
        {body}
      </div>
      <div style="padding:14px 24px;border-top:1px solid #e2e8f0;color:#94a3b8;font-size:12px;">
        Seller Management SaaS — multi-tenant seller platform
      </div>
    </div>
  </body>
</html>
"""


def _link(path: str) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}{path}"


def send_email(to: str, subject: str, html: str) -> bool:
    """Send an email; returns True when accepted (or simulated)."""
    if not settings.email_enabled or not settings.smtp_host:
        logger.info(
            "[email disabled] to=%s subject=%r — configure SMTP to deliver",
            to,
            subject,
        )
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content("This email requires HTML support.", subtype="plain")
    msg.add_alternative(html, subtype="html")

    try:
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def render(body_html: str) -> str:
    return EMAIL_TEMPLATE.format(body=body_html)


def send_verification_email(to: str, token: str) -> bool:
    link = _link(f"/verify-email?token={token}")
    return send_email(
        to,
        "Verify your email",
        render(
            f"<h2 style='margin:0 0 12px;color:#0f172a;font-size:18px;'>Verify your email</h2>"
            f"<p style='color:#475569;font-size:14px;line-height:1.6;'>"
            f"Welcome to Seller Manager! Confirm your email address to activate "
            f"your account.</p>"
            f"<p style='text-align:center;margin:24px 0;'>"
            f"<a href='{link}' style='background:#4f46e5;color:#ffffff;text-decoration:none;"
            f"padding:12px 28px;border-radius:8px;font-size:14px;font-weight:bold;'>"
            f"Verify email</a></p>"
            f"<p style='color:#94a3b8;font-size:12px;'>This link expires in 24 hours.</p>"
        ),
    )


def send_reset_password_email(to: str, token: str) -> bool:
    link = _link(f"/reset-password?token={token}")
    return send_email(
        to,
        "Reset your password",
        render(
            f"<h2 style='margin:0 0 12px;color:#0f172a;font-size:18px;'>Reset your password</h2>"
            f"<p style='color:#475569;font-size:14px;line-height:1.6;'>"
            f"We received a request to reset the password for <b>{to}</b>. "
            f"Click below to choose a new one.</p>"
            f"<p style='text-align:center;margin:24px 0;'>"
            f"<a href='{link}' style='background:#4f46e5;color:#ffffff;text-decoration:none;"
            f"padding:12px 28px;border-radius:8px;font-size:14px;font-weight:bold;'>"
            f"Reset password</a></p>"
            f"<p style='color:#94a3b8;font-size:12px;'>This link expires in 1 hour. "
            f"If you did not request this, you can ignore this email.</p>"
        ),
    )


def send_invite_email(to: str, token: str, organization_name: str, role_names: list[str]) -> bool:
    link = _link(f"/accept-invite?token={token}")
    return send_email(
        to,
        f"You've been invited to {organization_name}",
        render(
            f"<h2 style='margin:0 0 12px;color:#0f172a;font-size:18px;'>Team invitation</h2>"
            f"<p style='color:#475569;font-size:14px;line-height:1.6;'>"
            f"You've been invited to join <b>{organization_name}</b> as "
            f"<b>{', '.join(role_names)}</b>.</p>"
            f"<p style='text-align:center;margin:24px 0;'>"
            f"<a href='{link}' style='background:#4f46e5;color:#ffffff;text-decoration:none;"
            f"padding:12px 28px;border-radius:8px;font-size:14px;font-weight:bold;'>"
            f"Accept invitation</a></p>"
            f"<p style='color:#94a3b8;font-size:12px;'>This link expires in 72 hours.</p>"
        ),
    )
