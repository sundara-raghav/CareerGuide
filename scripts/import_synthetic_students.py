import csv
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.quiz import QuizAttempt, AptitudeScore
from werkzeug.security import generate_password_hash

app = create_app(os.getenv("FLASK_ENV", "development"))

def import_students():
    csv_path = Path(__file__).parent.parent / "data" / "synthetic_students.csv"
    if not csv_path.exists():
        print(f"CSV file not found at: {csv_path}")
        return

    print("Reading synthetic students CSV...")
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} records from CSV.")
    default_password_hash = generate_password_hash("password123")

    with app.app_context():
        # Get existing synthetic emails to avoid duplicates
        existing_emails = {
            u.email for u in db.session.query(User.email).filter(User.email.like("%@synthetic.in")).all()
        }
        print(f"Found {len(existing_emails)} existing synthetic students in database.")

        count = 0
        for i, row in enumerate(rows):
            student_id = row['student_id']
            email = f"student{student_id}@synthetic.in"

            if email in existing_emails:
                continue

            # Create User
            user = User(
                name=f"Student {student_id}",
                email=email,
                password_hash=default_password_hash,
                role=UserRole.STUDENT,
                phone=f"9000000{student_id.zfill(3)}",
                is_active=True,
                is_verified=True,
            )
            db.session.add(user)
            db.session.flush()

            # Process marks
            marks = {}
            mark_keys = [
                'mark_math', 'mark_science', 'mark_social', 'mark_english', 'mark_regional_language',
                'mark_core_subject_1', 'mark_core_subject_2', 'mark_elective_1', 'mark_elective_2'
            ]
            for key in mark_keys:
                val = row.get(key)
                if val is not None and val != '':
                    try:
                        marks[key] = float(val)
                    except ValueError:
                        pass

            # Process interests
            interest_cols = [col for col in row.keys() if col.startswith('interest_')]
            interests = [col.replace('interest_', '') for col in interest_cols if row[col].lower() == 'true']

            # Create Student profile
            student = Student(
                user_id=user.id,
                student_class=int(row['student_class']) if row.get('student_class') else None,
                board=row.get('board'),
                school_type=row.get('school_type', 'government'),
                district=row.get('district'),
                state="Tamil Nadu",
                aggregate_percentage=float(row['aggregate_percentage']) if row.get('aggregate_percentage') else None,
                annual_family_income=float(row['annual_family_income']) if row.get('annual_family_income') else None,
                budget_for_education=float(row['budget_for_education']) if row.get('budget_for_education') else None,
                travel_radius_km=float(row['travel_radius_km']) if row.get('travel_radius_km') else 50.0,
                needs_hostel=row.get('needs_hostel', '').lower() == 'true',
                needs_scholarship=row.get('needs_scholarship', '').lower() == 'true',
                marks=marks,
                interests=interests,
                stream_preference=row.get('target_stream'),
                career_goals=[row['target_career_cluster']] if row.get('target_career_cluster') else [],
                onboarding_complete=True,
                quiz_complete=True
            )
            db.session.add(student)
            db.session.flush()

            # Create Quiz Attempt
            attempt = QuizAttempt(
                student_id=student.id,
                is_complete=True,
                responses=[],
                completed_at=datetime.now(timezone.utc),
                time_taken_seconds=300
            )
            db.session.add(attempt)
            db.session.flush()

            # Parse Aptitude scores
            logical = float(row['apt_logical']) if row.get('apt_logical') else 0.0
            verbal = float(row['apt_verbal']) if row.get('apt_verbal') else 0.0
            quantitative = float(row['apt_quantitative']) if row.get('apt_quantitative') else 0.0
            social = float(row['apt_social']) if row.get('apt_social') else 0.0
            creative = float(row['apt_creative']) if row.get('apt_creative') else 0.0
            technical = float(row['apt_technical']) if row.get('apt_technical') else 0.0
            composite = (logical + verbal + quantitative + social + creative + technical) / 6.0

            # Create AptitudeScore
            apt_score = AptitudeScore(
                student_id=student.id,
                quiz_attempt_id=attempt.id,
                logical=logical,
                verbal=verbal,
                quantitative=quantitative,
                social=social,
                creative=creative,
                technical=technical,
                composite=composite
            )
            db.session.add(apt_score)

            count += 1
            if count % 100 == 0:
                db.session.commit()
                print(f"Imported {count} students...")

        if count > 0:
            db.session.commit()
            print(f"Successfully imported {count} new synthetic students into database!")
        else:
            print("No new students to import.")

if __name__ == "__main__":
    import_students()
