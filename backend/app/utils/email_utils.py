# app/utils/email_utils.py

import logging
from email.message import EmailMessage
from typing import Optional

import aiosmtplib

from app.config.settings import settings

logger = logging.getLogger("legalyze.email")


def _email_ready() -> bool:
    return bool(
        settings.EMAIL_ENABLED
        and settings.SMTP_SERVER
        and settings.SMTP_PORT
        and settings.FROM_EMAIL
    )


async def _send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
) -> bool:
    """
    Send an email using SMTP configuration from settings.
    Returns False when disabled/misconfigured or on send failure.
    """
    if not _email_ready():
        logger.warning(
            "Email send skipped: SMTP not configured or EMAIL_ENABLED=false | to=%s, subject=%s",
            to_email,
            subject,
        )
        return False

    message = EmailMessage()
    message["From"] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    smtp = aiosmtplib.SMTP(
        hostname=settings.SMTP_SERVER,
        port=int(settings.SMTP_PORT),
        timeout=settings.SMTP_TIMEOUT_SECONDS,
        use_tls=settings.SMTP_USE_TLS,
    )

    try:
        await smtp.connect()
        if settings.SMTP_USE_STARTTLS and not settings.SMTP_USE_TLS:
            await smtp.starttls()
        if settings.SMTP_USERNAME:
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        await smtp.send_message(message)
        logger.info("Email sent | to=%s, subject=%s", to_email, subject)
        return True
    except Exception as exc:
        logger.error("Email send failed | to=%s, subject=%s, error=%s", to_email, subject, exc)
        return False
    finally:
        try:
            await smtp.quit()
        except Exception:
            pass


async def send_verification_email(email: str, token: str) -> bool:
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your Legalyze account"
    text_body = (
        "Welcome to Legalyze.\n\n"
        f"Please verify your email using this link:\n{verification_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    html_body = (
        "<p>Welcome to <strong>Legalyze</strong>.</p>"
        f"<p>Please verify your email: <a href=\"{verification_url}\">{verification_url}</a></p>"
        "<p>If you did not create this account, ignore this email.</p>"
    )
    return await _send_email(email, subject, text_body, html_body)


async def send_password_reset_email(
    email: str,
    token: str | None = None,
    *,
    name: str | None = None,
    reset_token: str | None = None
) -> bool:
    effective_token = reset_token or token
    if not effective_token:
        logger.warning("Password reset email skipped: no token provided | email=%s", email)
        return False

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={effective_token}"
    greeting = f"Hi {name}," if name else "Hi,"
    subject = "Reset your Legalyze password"
    text_body = (
        f"{greeting}\n\n"
        "We received a request to reset your password.\n"
        f"Reset link (valid for 15 minutes):\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    html_body = (
        f"<p>{greeting}</p>"
        "<p>We received a request to reset your password.</p>"
        f"<p>Reset link (valid for 15 minutes): <a href=\"{reset_url}\">{reset_url}</a></p>"
        "<p>If you did not request this, you can ignore this email.</p>"
    )
    return await _send_email(email, subject, text_body, html_body)


async def send_welcome_email(email: str, name: str) -> bool:
    subject = "Welcome to Legalyze"
    text_body = (
        f"Hi {name},\n\n"
        "Welcome to Legalyze. You can now upload, analyze, and generate legal contracts securely."
    )
    html_body = (
        f"<p>Hi {name},</p>"
        "<p>Welcome to <strong>Legalyze</strong>. You can now upload, analyze, and generate legal contracts securely.</p>"
    )
    return await _send_email(email, subject, text_body, html_body)


async def send_countersign_request_email(
    email: str | None = None,
    contract_name: str | None = None,
    signer_name: str | None = None,
    *,
    to_email: str | None = None,
    to_name: str | None = None,
    from_name: str | None = None,
    contract_id: str | None = None,
    invite_token: str | None = None,
    expires_hours: int | None = None,
    personal_message: str | None = None
) -> bool:
    recipient = to_email or email
    if not recipient:
        logger.warning("Countersign email skipped: no recipient")
        return False

    contract_label = contract_name or contract_id or "contract"
    sender_name = from_name or signer_name or "A party"
    invite_url = (
        f"{settings.FRONTEND_URL}/signature/{contract_id}?invite={invite_token}"
        if contract_id and invite_token
        else None
    )
    expires_text = f"{expires_hours} hours" if expires_hours else "the configured expiry window"
    greeting = f"Hi {to_name}," if to_name else "Hi,"

    subject = f"Countersignature request for {contract_label}"
    text_parts = [
        greeting,
        "",
        f"{sender_name} requested your countersignature for {contract_label}.",
    ]
    if personal_message:
        text_parts += ["", f"Message from sender: {personal_message}"]
    if invite_url:
        text_parts += ["", f"Sign here (expires in {expires_text}):", invite_url]
    text_parts += ["", "If you were not expecting this request, ignore this email."]
    text_body = "\n".join(text_parts)

    html_body = (
        f"<p>{greeting}</p>"
        f"<p><strong>{sender_name}</strong> requested your countersignature for <strong>{contract_label}</strong>.</p>"
        + (f"<p>Message from sender: {personal_message}</p>" if personal_message else "")
        + (f"<p>Sign here (expires in {expires_text}): <a href=\"{invite_url}\">{invite_url}</a></p>" if invite_url else "")
        + "<p>If you were not expecting this request, ignore this email.</p>"
    )

    return await _send_email(recipient, subject, text_body, html_body)
