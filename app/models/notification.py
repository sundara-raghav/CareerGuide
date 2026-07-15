"""Notification model."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.extensions import db


class Notification(db.Model):
    """
    In-app notification record. Also serves as audit log for sent emails/SMS.
    payload_json stores channel-specific data (email subject/body, SMS text, etc.)
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    channel: Mapped[str] = mapped_column(String(20))  # email/sms/whatsapp/inapp
    notification_type: Mapped[str] = mapped_column(String(50))  # deadline/recommendation/scholarship/reminder

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(String(1000))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/sent/failed
    error_message: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="notifications")  # noqa: F821

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "type": self.notification_type,
            "title": self.title,
            "body": self.body,
            "is_read": self.is_read,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
