"""Student and Parent profile models."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.extensions import db


class Student(db.Model):
    """
    Extended student profile linked to a User.
    Stores academic background, location, and preferences.
    """

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    student_class: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 10 or 12
    board: Mapped[str | None] = mapped_column(String(50), nullable=True)  # CBSE, State, ICSE
    school_name: Mapped[str | None] = mapped_column(String(255))
    school_type: Mapped[str] = mapped_column(String(20), default="government")  # government/private

    # Academic marks stored as JSON: {"math": 85, "science": 78, "english": 90, ...}
    marks: Mapped[dict] = mapped_column(JSON, default=dict)
    aggregate_percentage: Mapped[float | None] = mapped_column(Float)

    # Location
    district: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    pincode: Mapped[str | None] = mapped_column(String(10))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    travel_radius_km: Mapped[float] = mapped_column(Float, default=50.0)

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    stream_preference: Mapped[str | None] = mapped_column(String(50))  # preferred stream if any
    interests: Mapped[list] = mapped_column(JSON, default=list)
    career_goals: Mapped[list] = mapped_column(JSON, default=list)

    # Constraints
    annual_family_income: Mapped[float | None] = mapped_column(Float)
    budget_for_education: Mapped[float | None] = mapped_column(Float)
    needs_hostel: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_scholarship: Mapped[bool] = mapped_column(Boolean, default=False)

    # Profile completion
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    quiz_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_score: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student_profile")  # noqa: F821
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(  # noqa: F821
        "QuizAttempt", back_populates="student", cascade="all, delete-orphan"
    )
    aptitude_score: Mapped["AptitudeScore | None"] = relationship(  # noqa: F821
        "AptitudeScore", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="student", cascade="all, delete-orphan"
    )
    admission_events: Mapped[list["AdmissionEvent"]] = relationship(  # noqa: F821
        "AdmissionEvent", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} class={self.student_class}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_class": self.student_class,
            "board": self.board,
            "aggregate_percentage": self.aggregate_percentage,
            "district": self.district,
            "state": self.state,
            "travel_radius_km": self.travel_radius_km,
            "interests": self.interests,
            "budget_for_education": self.budget_for_education,
            "onboarding_complete": self.onboarding_complete,
            "quiz_complete": self.quiz_complete,
        }


class Parent(db.Model):
    """Parent profile linked to a User and optionally a Student."""

    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    linked_student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"))
    occupation: Mapped[str | None] = mapped_column(String(100))
    annual_income: Mapped[float | None] = mapped_column(Float)
    education_level: Mapped[str | None] = mapped_column(String(100))
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="parent_profile")  # noqa: F821
    linked_student: Mapped["Student | None"] = relationship("Student", foreign_keys=[linked_student_id])


class AdmissionEvent(db.Model):
    """Tracks a student's application/admission status at a college."""

    __tablename__ = "admission_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False)
    course_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(
        db.Enum('shortlisted', 'applied', 'admitted', 'rejected', name='admission_status'), default='shortlisted'
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    admission_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["Student"] = relationship("Student", back_populates="admission_events")
    college: Mapped["College"] = relationship("College")  # noqa: F821
