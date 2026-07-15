"""
Create demo/sample login accounts for local testing.

Run:  python scripts/create_demo_users.py

Demo credentials
────────────────
Role        Email                       Password
─────────── ─────────────────────────── ─────────────
student     student@demo.com            Demo@1234
parent      parent@demo.com             Demo@1234
counselor   counselor@demo.com          Demo@1234
admin       admin@demo.com              Admin@1234
"""
import os
import sys

# Make sure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.student import Student
from app.models.user import User, UserRole
from werkzeug.security import generate_password_hash

DEMO_USERS = [
    {
        "name": "Arjun Kumar (Student)",
        "email": "student@demo.com",
        "password": "Demo@1234",
        "role": UserRole.STUDENT,
        "phone": "9876543210",
    },
    {
        "name": "Meena Kumar (Parent)",
        "email": "parent@demo.com",
        "password": "Demo@1234",
        "role": UserRole.PARENT,
        "phone": "9876543211",
    },
    {
        "name": "Dr. Priya (Counselor)",
        "email": "counselor@demo.com",
        "password": "Demo@1234",
        "role": UserRole.COUNSELOR,
        "phone": "9876543212",
    },
    {
        "name": "Admin User",
        "email": "admin@demo.com",
        "password": "Admin@1234",
        "role": UserRole.ADMIN,
        "phone": "9876543213",
    },
]


def create_demo_users():
    app = create_app("development")
    with app.app_context():
        db.create_all()
        created = []
        skipped = []

        for u in DEMO_USERS:
            existing = db.session.query(User).filter_by(email=u["email"]).first()
            if existing:
                skipped.append(u["email"])
                continue

            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"]),
                role=u["role"],
                phone=u["phone"],
                is_active=True,
            )
            db.session.add(user)
            db.session.flush()

            # Create student profile for student role
            if u["role"] == UserRole.STUDENT:
                student = Student(
                    user_id=user.id,
                    student_class=12,
                    board="CBSE",
                    state="Tamil Nadu",
                    district="Chennai",
                    stream_preference="Science",
                )
                db.session.add(student)

            created.append(u["email"])

        db.session.commit()

        print("\n" + "=" * 55)
        print("  CareerGuide India -- Demo Accounts")
        print("=" * 55)

        if created:
            print(f"\n[OK] Created {len(created)} demo account(s):\n")
            print(f"  {'Role':<12} {'Email':<28} {'Password'}")
            print(f"  {'----':<12} {'-----':<28} {'--------'}")
            for u in DEMO_USERS:
                if u["email"] in created:
                    print(f"  {u['role'].value:<12} {u['email']:<28} {u['password']}")

        if skipped:
            print(f"\n[SKIP] Already exist: {', '.join(skipped)}")

        print("\n" + "=" * 55)
        print("  Open: http://127.0.0.1:5000/auth/login")
        print("=" * 55 + "\n")


if __name__ == "__main__":
    create_demo_users()
