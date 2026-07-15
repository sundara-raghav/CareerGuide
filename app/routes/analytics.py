"""Analytics blueprint."""

from flask import Blueprint, jsonify
from flask_login import login_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/impact")
def impact():
    from app.extensions import db
    from app.models.college import College
    from app.models.recommendation import Recommendation
    from app.models.student import Student

    return jsonify(
        {
            "students_guided": db.session.query(Student).count(),
            "recommendations_made": db.session.query(Recommendation).count(),
            "colleges_listed": db.session.query(College).count(),
        }
    )


@analytics_bp.route("/api/district-heatmap")
@login_required
def district_heatmap():
    from app.repositories.student_repo import StudentRepository

    data = StudentRepository().count_by_district()
    return jsonify(data)
