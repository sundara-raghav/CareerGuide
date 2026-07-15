"""College and course models."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.extensions import db


class College(db.Model):
    """
    College record with location, fees, courses, and cutoffs.
    Latitude/longitude enable Google Maps distance calculations.
    """

    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, nullable=False, index=True)

    # Type
    college_type: Mapped[str] = mapped_column(String(30), default="government")  # government/private/aided
    accreditation: Mapped[str | None] = mapped_column(String(50))  # NAAC A+/A/B etc.

    # Location
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(10))
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    google_place_id: Mapped[str | None] = mapped_column(String(200))

    # Courses offered: [{name, type, duration, seats, annual_fees, medium}]
    courses_offered: Mapped[list] = mapped_column(JSON, default=list)

    # Cutoff data: {2024: {"Science": 85.5, "Commerce": 75.0}}
    cutoff_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # Fees
    annual_fees_min: Mapped[float | None] = mapped_column(Float)
    annual_fees_max: Mapped[float | None] = mapped_column(Float)

    # Facilities
    has_hostel: Mapped[bool] = mapped_column(Boolean, default=False)
    has_transport: Mapped[bool] = mapped_column(Boolean, default=False)
    medium_of_instruction: Mapped[list] = mapped_column(JSON, default=list)  # ["Tamil", "English"]

    # Metadata
    website: Mapped[str | None] = mapped_column(String(300))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    established_year: Mapped[int | None] = mapped_column(Integer)
    total_seats: Mapped[int | None] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<College {self.name} [{self.college_type}]>"

    def to_dict(self, include_distance: float | None = None) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "college_type": self.college_type,
            "district": self.district,
            "state": self.state,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "annual_fees_min": self.annual_fees_min,
            "annual_fees_max": self.annual_fees_max,
            "has_hostel": self.has_hostel,
            "medium_of_instruction": self.medium_of_instruction,
            "courses_offered": self.courses_offered,
            "cutoff_data": self.cutoff_data,
            "accreditation": self.accreditation,
            "website": self.website,
        }
        if include_distance is not None:
            data["distance_km"] = round(include_distance, 1)
        return data


class Scholarship(db.Model):
    """
    Scholarship records with eligibility criteria and deadlines.
    Eligibility stored as JSON rules engine-compatible dict.
    """

    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    provider: Mapped[str] = mapped_column(String(200), nullable=False)
    scheme_type: Mapped[str] = mapped_column(String(50))  # central/state/private/NGO

    # Eligibility rules: {class: [10,12], income_max: 250000, caste: ["SC","ST","OBC"], marks_min: 60}
    eligibility_criteria: Mapped[dict] = mapped_column(JSON, default=dict)

    amount: Mapped[float | None] = mapped_column(Float)
    amount_description: Mapped[str | None] = mapped_column(String(300))  # "Full tuition waiver"
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_link: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "scheme_type": self.scheme_type,
            "amount": self.amount,
            "amount_description": self.amount_description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "application_link": self.application_link,
            "description": self.description,
            "eligibility_criteria": self.eligibility_criteria,
        }
