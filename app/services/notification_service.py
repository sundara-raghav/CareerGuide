"""Notification service — multi-channel event-driven notifications."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import structlog

from app.extensions import db
from app.models.notification import Notification
from app.models.user import User

log = structlog.get_logger(__name__)


class NotificationService:
    """
    Abstraction over email/SMS/WhatsApp/in-app channels.
    Each channel is pluggable — real providers called only if credentials exist.
    Celery-ready: methods can be wrapped in Celery tasks for async delivery.
    """

    def send(
        self,
        user: User,
        notification_type: str,
        title: str,
        body: str,
        channels: list[str] | None = None,
        payload: dict | None = None,
    ) -> list[Notification]:
        channels = channels or ["inapp"]
        sent: list[Notification] = []

        for channel in channels:
            notif = Notification(
                user_id=user.id,
                channel=channel,
                notification_type=notification_type,
                title=title,
                body=body,
                payload=payload or {},
                status="pending",
            )
            db.session.add(notif)
            db.session.flush()

            try:
                if channel == "email":
                    self._send_email(user.email, title, body)
                elif channel == "sms":
                    self._send_sms(user.phone, body)
                elif channel == "whatsapp":
                    self._send_whatsapp(user.phone, body)
                # inapp: stored in DB, polled by frontend

                notif.status = "sent"
                notif.sent_at = datetime.now(timezone.utc)

            except Exception as exc:
                log.error("Notification send failed", channel=channel, error=str(exc))
                notif.status = "failed"
                notif.error_message = str(exc)[:500]

            sent.append(notif)

        db.session.commit()
        return sent

    def _send_email(self, to_email: str, subject: str, body: str) -> None:
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            log.warning("SendGrid API key not configured — skipping email")
            return

        import sendgrid
        from sendgrid.helpers.mail import Content, Mail, To

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        mail = Mail(
            from_email=os.getenv("MAIL_DEFAULT_SENDER", "no-reply@careerguide.in"),
            to_emails=to_email,
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )
        response = sg.client.mail.send.post(request_body=mail.get())
        if response.status_code not in (200, 202):
            raise RuntimeError(f"SendGrid returned {response.status_code}")

    def _send_sms(self, phone: str | None, body: str) -> None:
        if not phone:
            return
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not account_sid or not auth_token:
            log.warning("Twilio not configured — skipping SMS")
            return

        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=body,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=phone,
        )

    def _send_whatsapp(self, phone: str | None, body: str) -> None:
        if not phone:
            return
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not account_sid or not auth_token:
            log.warning("Twilio not configured — skipping WhatsApp")
            return

        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=body,
            from_=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"),
            to=f"whatsapp:{phone}",
        )

    def get_unread(self, user_id: int) -> list[Notification]:
        return (
            db.session.query(Notification)
            .filter_by(user_id=user_id, is_read=False, channel="inapp")
            .order_by(Notification.created_at.desc())
            .limit(20)
            .all()
        )

    def mark_read(self, notification_id: int, user_id: int) -> bool:
        notif = db.session.query(Notification).filter_by(id=notification_id, user_id=user_id).first()
        if not notif:
            return False
        notif.is_read = True
        db.session.commit()
        return True


# ── Celery task wrappers (import celery only if available) ─────────────────────
try:
    from celery import shared_task

    @shared_task(bind=True, max_retries=3, default_retry_delay=60)
    def send_notification_task(self, user_id: int, notification_type: str, title: str, body: str, channels: list[str], payload: dict):
        from app.models.user import User
        user = db.session.get(User, user_id)
        if user:
            NotificationService().send(user, notification_type, title, body, channels, payload)

except ImportError:
    pass
