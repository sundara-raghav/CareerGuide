"""Admin blueprint — analytics dashboard, counselor tools."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models.recommendation import CounselorFeedback
from app.models.student import Student
from app.models.user import User, UserRole
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.student_repo import StudentRepository
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")
student_repo = StudentRepository()
rec_repo = RecommendationRepository()


@admin_bp.route("/dashboard")
@login_required
@role_required(UserRole.ADMIN)
def dashboard():
    stats = _get_platform_stats()
    district_data = student_repo.count_by_district()
    stream_dist = rec_repo.get_stream_distribution()
    acceptance_rate = rec_repo.get_acceptance_rate()
    recent_students = student_repo.get_all(limit=20)

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        district_data=district_data,
        stream_dist=stream_dist,
        acceptance_rate=acceptance_rate,
        recent_students=recent_students,
    )


@admin_bp.route("/counselor")
@login_required
@role_required(UserRole.COUNSELOR, UserRole.ADMIN)
def counselor_dashboard():
    students = student_repo.get_all(limit=50)
    return render_template("admin/counselor.html", students=students)


@admin_bp.route("/api/stats")
@login_required
@role_required(UserRole.ADMIN)
def api_stats():
    return jsonify(_get_platform_stats())


@admin_bp.route("/api/feedback", methods=["POST"])
@login_required
@role_required(UserRole.COUNSELOR, UserRole.ADMIN)
def submit_feedback():
    data = request.get_json()
    feedback = CounselorFeedback(
        student_id=data["student_id"],
        counselor_id=current_user.id,
        recommendation_id=data.get("recommendation_id"),
        notes=data["notes"],
        override_stream=data.get("override_stream"),
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"status": "ok"})


def _get_platform_stats() -> dict:
    total_students = db.session.query(Student).count()
    onboarded = db.session.query(Student).filter_by(onboarding_complete=True).count()
    quiz_done = db.session.query(Student).filter_by(quiz_complete=True).count()
    from app.models.recommendation import Recommendation
    total_recs = db.session.query(Recommendation).count()

    return {
        "total_students": total_students,
        "onboarding_rate": round(onboarded / max(total_students, 1) * 100, 1),
        "quiz_completion_rate": round(quiz_done / max(total_students, 1) * 100, 1),
        "total_recommendations": total_recs,
        "acceptance_rate": round(rec_repo.get_acceptance_rate() * 100, 1),
    }
