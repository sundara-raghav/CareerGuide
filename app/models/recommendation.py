"""Recommendation and model feedback models."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.extensions import db


class Recommendation(db.Model):
    """
    Top-5 ranked recommendations generated for a student.
    Stores stream, courses, careers with confidence scores and SHAP explanations.
    """

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)

    # Primary recommendation
    recommended_stream: Mapped[str] = mapped_column(String(50))  # Science/Arts/Commerce/Vocational
    stream_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Top-5 course recommendations: [{rank, course, degree_type, confidence, reasons: []}]
    top_courses: Mapped[list] = mapped_column(JSON, default=list)

    # Top-5 career clusters: [{rank, career, exams, salary_range, growth_outlook}]
    career_clusters: Mapped[list] = mapped_column(JSON, default=list)

    # Explanation data: {feature_importances: {}, shap_values: {}, rule_flags: []}
    explanations: Mapped[dict] = mapped_column(JSON, default=dict)

    # Scholarship eligibility scores: [{scholarship_id, name, score, eligible: bool}]
    scholarship_matches: Mapped[list] = mapped_column(JSON, default=list)

    # ML model version used
    model_version: Mapped[str] = mapped_column(String(20), default="v1")

    # User interaction
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shortlisted_courses: Mapped[list] = mapped_column(JSON, default=list)
    rejected_courses: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["Student"] = relationship("Student", back_populates="recommendations")  # noqa: F821
    feedback: Mapped[list["ModelFeedback"]] = relationship(
        "ModelFeedback", back_populates="recommendation", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "recommended_stream": self.recommended_stream,
            "stream_confidence": round(self.stream_confidence, 3),
            "top_courses": self.top_courses,
            "career_clusters": self.career_clusters,
            "explanations": self.explanations,
            "scholarship_matches": self.scholarship_matches,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat(),
        }


class ModelFeedback(db.Model):
    """
    Captures whether a student accepted/rejected a recommendation and actual outcome.
    Used to retrain and improve the ensemble model.
    """

    __tablename__ = "model_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)

    # What they chose vs what was recommended
    recommended_course: Mapped[str] = mapped_column(String(200))
    accepted: Mapped[bool | None] = mapped_column()  # None = no response yet
    actual_course_enrolled: Mapped[str | None] = mapped_column(String(200))
    actual_college: Mapped[str | None] = mapped_column(String(255))

    # Outcome (filled later during follow-up)
    outcome_satisfied: Mapped[bool | None] = mapped_column()
    outcome_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="feedback")


class CounselorFeedback(db.Model):
    """Manual review notes from a counselor on a student's recommendation."""

    __tablename__ = "counselor_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    counselor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.id"))
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    override_stream: Mapped[str | None] = mapped_column(String(50))
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
