"""Test fixtures and app factory for the test suite."""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.college import College


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Provide clean DB per test function."""
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_user(db):
    from werkzeug.security import generate_password_hash
    user = User(
        name="Test Student",
        email="test@example.com",
        password_hash=generate_password_hash("password123"),
        role=UserRole.STUDENT,
    )
    db.session.add(user)
    db.session.flush()
    student = Student(
        user_id=user.id,
        student_class=12,
        board="CBSE",
        aggregate_percentage=78.5,
        marks={"math": 85, "science": 82, "english": 75, "social": 72, "regional_language": 78},
        district="Chennai",
        state="Tamil Nadu",
        travel_radius_km=50,
        annual_family_income=200000,
        budget_for_education=50000,
        interests=["mathematics", "computers"],
        onboarding_complete=True,
    )
    db.session.add(student)
    db.session.commit()
    return user


@pytest.fixture
def sample_college(db):
    college = College(
        name="Government Arts College",
        slug="government-arts-college-chennai",
        college_type="government",
        district="Chennai",
        state="Tamil Nadu",
        latitude=13.0827,
        longitude=80.2707,
        annual_fees_min=5000,
        annual_fees_max=15000,
        has_hostel=True,
        courses_offered=[{"name": "BA English", "type": "undergraduate", "seats": 60}],
        medium_of_instruction=["Tamil", "English"],
    )
    db.session.add(college)
    db.session.commit()
    return college
