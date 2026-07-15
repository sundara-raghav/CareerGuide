"""Remaining blueprints: careers, notifications, analytics."""

from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

from app.services.notification_service import NotificationService
from app.services.recommendation_service import RecommendationService

# ── Careers ────────────────────────────────────────────────────────────────────
careers_bp = Blueprint("careers", __name__, template_folder="../templates/careers")
rec_svc = RecommendationService()


@careers_bp.route("/roadmap/<path:course_name>")
@login_required
def roadmap(course_name: str):
    roadmap_data = rec_svc.get_career_roadmap(course_name)
    return render_template("careers/roadmap.html", roadmap=roadmap_data, course_name=course_name)


@careers_bp.route("/api/roadmap/<path:course_name>")
@login_required
def roadmap_api(course_name: str):
    return jsonify(rec_svc.get_career_roadmap(course_name))


# ── Notifications ──────────────────────────────────────────────────────────────
notifications_bp = Blueprint("notifications", __name__)
notif_svc = NotificationService()


@notifications_bp.route("/api/unread")
@login_required
def unread():
    notifs = notif_svc.get_unread(current_user.id)
    return jsonify([n.to_dict() for n in notifs])


@notifications_bp.route("/api/mark-read/<int:notif_id>", methods=["POST"])
@login_required
def mark_read(notif_id: int):
    ok = notif_svc.mark_read(notif_id, current_user.id)
    return jsonify({"status": "ok" if ok else "not_found"})


# ── Analytics ──────────────────────────────────────────────────────────────────
analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/impact")
@login_required
def impact():
    """Public impact metrics for the landing page counter."""
    from app.extensions import db
    from app.models.recommendation import Recommendation
    from app.models.student import Student

    return jsonify(
        {
            "students_guided": db.session.query(Student).count(),
            "recommendations_made": db.session.query(Recommendation).count(),
            "colleges_listed": db.session.query(__import__("app.models.college", fromlist=["College"]).College).count(),
        }
    )


@analytics_bp.route("/api/district-heatmap")
@login_required
def district_heatmap():
    from app.repositories.student_repo import StudentRepository

    data = StudentRepository().count_by_district()
    return jsonify(data)
