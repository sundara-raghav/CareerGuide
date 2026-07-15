"""Student blueprint — onboarding wizard, quiz, dashboard."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.student import Student
from app.services.quiz_service import QuizService
from app.services.recommendation_service import RecommendationService

student_bp = Blueprint("student", __name__, template_folder="../templates/student")
quiz_svc = QuizService()
rec_svc = RecommendationService()


DISTRICT_COORDS = {
    "chennai": (13.0827, 80.2707),
    "coimbatore": (11.0168, 76.9558),
    "madurai": (9.9252, 78.1198),
    "trichy": (10.7905, 78.7047),
    "tiruchirappalli": (10.7905, 78.7047),
    "salem": (11.6643, 78.1460),
    "tirunelveli": (8.7139, 77.7567),
    "erode": (11.3410, 77.7172),
    "vellore": (12.9165, 79.1325),
    "thanjavur": (10.7870, 79.1378),
    "kanchipuram": (12.8342, 79.7036),
    "villupuram": (11.9401, 79.4861),
    "dharmapuri": (12.1211, 78.1582),
    "namakkal": (11.2189, 78.1674),
    "karur": (10.9601, 78.0766),
    "dindigul": (10.3673, 77.9803),
    "ariyalur": (11.1378, 79.0743),
    "perambalur": (11.2342, 78.8836),
    "cuddalore": (11.7480, 79.7714),
}


@student_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    student = current_user.student_profile
    if not student:
        flash("Student profile not found.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        step = int(request.form.get("step", 1))
        _save_onboarding_step(student, step, request.form)
        db.session.commit()

        if step < 4:
            return render_template("student/onboarding.html", student=student, step=step + 1)

        student.onboarding_complete = True
        db.session.commit()
        flash("Profile complete! Now take the aptitude quiz.", "success")
        return redirect(url_for("student.quiz"))

    step = int(request.args.get("step", 1))
    return render_template("student/onboarding.html", student=student, step=step)


@student_bp.route("/quiz", methods=["GET"])
@login_required
def quiz():
    student = current_user.student_profile
    if not student or not student.onboarding_complete:
        flash("Please complete your profile first.", "warning")
        return redirect(url_for("student.onboarding"))

    questions = quiz_svc.get_questions()
    sections = quiz_svc.get_sections()
    attempt = quiz_svc.start_attempt(student.id)
    return render_template("student/quiz.html", questions=questions, sections=sections, attempt_id=attempt.id)


@student_bp.route("/quiz/submit", methods=["POST"])
@login_required
def quiz_submit():
    student = current_user.student_profile
    attempt_id = request.form.get("attempt_id", type=int)
    responses = []

    for key, value in request.form.items():
        if key.startswith("q_"):
            try:
                question_id = int(key[2:])
                responses.append({"question_id": question_id, "selected_key": value})
            except (ValueError, IndexError):
                pass

    try:
        quiz_svc.submit_attempt(attempt_id, responses)
        rec = rec_svc.generate_for_student(student)
        if rec:
            flash("Your personalized recommendations are ready!", "success")
        return redirect(url_for("recommendations.dashboard"))
    except Exception as exc:
        flash(f"Error processing quiz: {exc}", "danger")
        return redirect(url_for("student.quiz"))


@student_bp.route("/dashboard")
@login_required
def dashboard():
    student = current_user.student_profile
    latest_rec = None
    if student and student.quiz_complete:
        from app.repositories.recommendation_repo import RecommendationRepository

        latest_rec = RecommendationRepository().get_latest_for_student(student.id)

    return render_template(
        "student/dashboard.html",
        student=student,
        recommendation=latest_rec,
        user=current_user,
    )


def _save_onboarding_step(student: Student, step: int, form) -> None:
    """Map form fields to student model per wizard step."""
    if step == 1:
        student.student_class = form.get("student_class", type=int)
        student.board = form.get("board", "")
        student.school_name = form.get("school_name", "")
        student.school_type = form.get("school_type", "government")
    elif step == 2:
        marks_raw = {k[5:]: float(v) for k, v in form.items() if k.startswith("mark_") and v}
        student.marks = marks_raw
        if marks_raw:
            student.aggregate_percentage = round(sum(marks_raw.values()) / len(marks_raw), 1)
    elif step == 3:
        district = form.get("district", "").strip()
        student.district = district
        student.state = form.get("state", "Tamil Nadu")
        student.pincode = form.get("pincode", "")
        student.travel_radius_km = form.get("travel_radius_km", type=float, default=50.0)

        # Geocode the district to latitude and longitude
        coords = DISTRICT_COORDS.get(district.lower())
        if coords:
            student.latitude = coords[0]
            student.longitude = coords[1]
        else:
            # Default fallback coords
            student.latitude = 11.0168
            student.longitude = 76.9558
    elif step == 4:
        student.interests = form.getlist("interests")
        student.annual_family_income = form.get("annual_family_income", type=float)
        student.budget_for_education = form.get("budget_for_education", type=float)
        student.needs_hostel = bool(form.get("needs_hostel"))
        student.needs_scholarship = bool(form.get("needs_scholarship"))
