"""Quiz and aptitude score models."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.extensions import db


class QuizAttempt(db.Model):
    """
    Records one attempt of the aptitude quiz by a student.
    Responses stored as JSON array: [{question_id, answer, section}]
    """

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    responses: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer)
    is_complete: Mapped[bool] = mapped_column(default=False)

    student: Mapped["Student"] = relationship("Student", back_populates="quiz_attempts")  # noqa: F821
    aptitude_score: Mapped["AptitudeScore | None"] = relationship(
        "AptitudeScore", back_populates="quiz_attempt", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} student_id={self.student_id} complete={self.is_complete}>"


class AptitudeScore(db.Model):
    """
    Normalized aptitude scores (0-100) per section, derived from a QuizAttempt.
    These feed directly into the ML recommendation engine.
    """

    __tablename__ = "aptitude_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True, nullable=False)
    quiz_attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id"), nullable=False)

    # Section scores (0–100)
    logical: Mapped[float] = mapped_column(Float, default=0.0)
    verbal: Mapped[float] = mapped_column(Float, default=0.0)
    quantitative: Mapped[float] = mapped_column(Float, default=0.0)
    social: Mapped[float] = mapped_column(Float, default=0.0)
    creative: Mapped[float] = mapped_column(Float, default=0.0)
    technical: Mapped[float] = mapped_column(Float, default=0.0)

    # Composite score
    composite: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["Student"] = relationship("Student", back_populates="aptitude_score")  # noqa: F821
    quiz_attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="aptitude_score")

    def to_feature_vector(self) -> dict:
        """Returns a dict suitable for ML feature input."""
        return {
            "aptitude_logical": self.logical,
            "aptitude_verbal": self.verbal,
            "aptitude_quantitative": self.quantitative,
            "aptitude_social": self.social,
            "aptitude_creative": self.creative,
            "aptitude_technical": self.technical,
            "aptitude_composite": self.composite,
        }
