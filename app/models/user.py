"""SQLAlchemy ORM models — User and authentication."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db, login_manager


class UserRole(str, PyEnum):
    STUDENT = "student"
    PARENT = "parent"
    COUNSELOR = "counselor"
    ADMIN = "admin"


class User(UserMixin, db.Model):
    """
    Core user record. One-to-one with Student, Parent, etc.
    Auth is handled by Supabase JWT; this table stores profile metadata.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    supabase_uid: Mapped[str] = mapped_column(String(64), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), default=UserRole.STUDENT, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    password_hash: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    student_profile: Mapped["Student | None"] = relationship(  # noqa: F821
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    parent_profile: Mapped["Parent | None"] = relationship(  # noqa: F821
        "Parent", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "preferred_language": self.preferred_language,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))
