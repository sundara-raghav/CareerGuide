"""
Database seed script — populates colleges, scholarships, and sample users.
Run: python scripts/seed_db.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.college import College, Scholarship
from app.models.student import Student
from app.models.user import User, UserRole

app = create_app(os.getenv("FLASK_ENV", "development"))


COLLEGES_SEED = [
    {
        "name": "Government Arts College, Chennai",
        "slug": "govt-arts-college-chennai",
        "college_type": "government",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "annual_fees_min": 5000,
        "annual_fees_max": 12000,
        "has_hostel": True,
        "courses_offered": [
            {"name": "BA English", "seats": 60},
            {"name": "BA History", "seats": 60},
            {"name": "BCom", "seats": 60},
        ],
        "medium_of_instruction": ["Tamil", "English"],
    },
    {
        "name": "PSG College of Technology, Coimbatore",
        "slug": "psg-tech-coimbatore",
        "college_type": "aided",
        "district": "Coimbatore",
        "state": "Tamil Nadu",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "annual_fees_min": 35000,
        "annual_fees_max": 70000,
        "has_hostel": True,
        "courses_offered": [{"name": "BTech/BE", "seats": 120}, {"name": "BCA", "seats": 60}],
        "medium_of_instruction": ["English"],
    },
    {
        "name": "Madurai Kamaraj University, Madurai",
        "slug": "mku-madurai",
        "college_type": "government",
        "district": "Madurai",
        "state": "Tamil Nadu",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "annual_fees_min": 8000,
        "annual_fees_max": 25000,
        "has_hostel": True,
        "courses_offered": [
            {"name": "BSc Physics", "seats": 40},
            {"name": "BSc Chemistry", "seats": 40},
            {"name": "BA Economics", "seats": 60},
        ],
        "medium_of_instruction": ["Tamil", "English"],
    },
    {
        "name": "Thiagarajar College of Engineering, Madurai",
        "slug": "tce-madurai",
        "college_type": "aided",
        "district": "Madurai",
        "state": "Tamil Nadu",
        "latitude": 9.8892,
        "longitude": 78.1234,
        "annual_fees_min": 40000,
        "annual_fees_max": 80000,
        "has_hostel": True,
        "courses_offered": [{"name": "BTech/BE", "seats": 180}],
        "medium_of_instruction": ["English"],
    },
    {
        "name": "Government Polytechnic College, Salem",
        "slug": "govt-polytechnic-salem",
        "college_type": "government",
        "district": "Salem",
        "state": "Tamil Nadu",
        "latitude": 11.6643,
        "longitude": 78.1460,
        "annual_fees_min": 2000,
        "annual_fees_max": 5000,
        "has_hostel": False,
        "courses_offered": [{"name": "Diploma Engineering", "seats": 60}, {"name": "Polytechnic", "seats": 60}],
        "medium_of_instruction": ["Tamil", "English"],
    },
]

SCHOLARSHIPS_SEED = [
    {
        "name": "Tamil Nadu Government Free Education Scheme",
        "provider": "Government of Tamil Nadu",
        "scheme_type": "state",
        "eligibility_criteria": {"class": [10, 12], "school_type": ["government"], "income_max": 250000},
        "amount": 12000,
        "amount_description": "Full tuition waiver + ₹12,000/year stipend",
        "description": "For students from government schools with family income below ₹2.5 lakh.",
    },
    {
        "name": "Post-Matric Scholarship for SC/ST",
        "provider": "Ministry of Social Justice",
        "scheme_type": "central",
        "eligibility_criteria": {"class": [12], "caste": ["SC", "ST"], "income_max": 250000},
        "amount": 30000,
        "amount_description": "Up to ₹30,000/year for tuition and maintenance",
        "description": "Central government scholarship for SC/ST students pursuing higher education.",
    },
    {
        "name": "NSP Merit-cum-Means Scholarship",
        "provider": "National Scholarship Portal",
        "scheme_type": "central",
        "eligibility_criteria": {"class": [12], "marks_min": 60, "income_max": 450000},
        "amount": 25000,
        "amount_description": "₹25,000/year for professional courses",
        "description": "For meritorious students from economically weaker sections.",
    },
    {
        "name": "AICTE Pragati Scholarship for Girls",
        "provider": "AICTE",
        "scheme_type": "central",
        "eligibility_criteria": {"class": [12], "gender": ["Female"], "income_max": 800000},
        "amount": 50000,
        "amount_description": "₹50,000/year for technical education",
        "description": "Empowering girl students to pursue technical education.",
    },
]


def seed():
    with app.app_context():
        # db.create_all()
        pass

        # Seed colleges
        existing_slugs = {c.slug for c in db.session.query(College).all()}
        for c_data in COLLEGES_SEED:
            if c_data["slug"] not in existing_slugs:
                college = College(**c_data)
                db.session.add(college)
        db.session.commit()
        print(f"Seeded {len(COLLEGES_SEED)} colleges")

        # Seed scholarships
        existing_names = {s.name for s in db.session.query(Scholarship).all()}
        for s_data in SCHOLARSHIPS_SEED:
            if s_data["name"] not in existing_names:
                scholarship = Scholarship(**s_data)
                db.session.add(scholarship)
        db.session.commit()
        print(f"Seeded {len(SCHOLARSHIPS_SEED)} scholarships")

        # Seed admin user
        if not db.session.query(User).filter_by(email="admin@careerguide.in").first():
            admin = User(
                name="Admin User",
                email="admin@careerguide.in",
                password_hash=generate_password_hash("admin123!"),
                role=UserRole.ADMIN,
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user: admin@careerguide.in / admin123!")

        # Seed demo student
        if not db.session.query(User).filter_by(email="student@demo.in").first():
            user = User(
                name="Priya Devi",
                email="student@demo.in",
                password_hash=generate_password_hash("demo1234"),
                role=UserRole.STUDENT,
            )
            db.session.add(user)
            db.session.flush()
            student = Student(
                user_id=user.id,
                student_class=12,
                board="State Board",
                school_type="government",
                district="Coimbatore",
                state="Tamil Nadu",
                aggregate_percentage=78.5,
                marks={
                    "mark_english": 82,
                    "mark_core_subject_1": 79,
                    "mark_core_subject_2": 75,
                    "mark_elective_1": 80,
                    "mark_elective_2": 77,
                },
                travel_radius_km=30,
                annual_family_income=150000,
                budget_for_education=30000,
                needs_scholarship=True,
                interests=["mathematics", "computers", "teaching"],
                onboarding_complete=True,
            )
            db.session.add(student)
            db.session.commit()
            print("Created demo student: student@demo.in / demo1234")

        print("\nDatabase seeded successfully!")
        print("Demo login -- Student: student@demo.in / demo1234")
        print("Admin login -- admin@careerguide.in / admin123!")


if __name__ == "__main__":
    seed()
