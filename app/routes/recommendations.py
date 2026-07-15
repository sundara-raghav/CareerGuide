"""Recommendations blueprint — dashboard, feedback, career details."""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models.recommendation import ModelFeedback
from app.repositories.recommendation_repo import RecommendationRepository
from app.services.recommendation_service import RecommendationService

recommendations_bp = Blueprint("recommendations", __name__, template_folder="../templates/recommendations")
rec_svc = RecommendationService()
rec_repo = RecommendationRepository()


@recommendations_bp.route("/dashboard")
@login_required
def dashboard():
    student = current_user.student_profile
    if not student:
        return render_template("errors/404.html"), 404

    recommendation = rec_repo.get_latest_for_student(student.id)

    if not recommendation and student.quiz_complete:
        # Generate if quiz done but no recommendation yet
        recommendation = rec_svc.generate_for_student(student)

    recommended_colleges = rec_svc.get_recommended_colleges(student, recommendation)

    return render_template(
        "recommendations/dashboard.html",
        student=student,
        recommendation=recommendation,
        recommended_colleges=recommended_colleges,
        user=current_user,
    )


@recommendations_bp.route("/api/feedback", methods=["POST"])
@login_required
def feedback():
    data = request.get_json()
    rec_id = data.get("recommendation_id")
    accepted = data.get("accepted")
    course = data.get("recommended_course", "")

    student = current_user.student_profile
    rec_svc.record_feedback(rec_id, student.id, accepted, course)
    return jsonify({"status": "ok"})


@recommendations_bp.route("/api/regenerate", methods=["POST"])
@login_required
def regenerate():
    student = current_user.student_profile
    if not student or not student.quiz_complete:
        return jsonify({"error": "Complete the quiz first"}), 400
    rec = rec_svc.generate_for_student(student)
    return jsonify(rec.to_dict() if rec else {"error": "Failed to generate"})


@recommendations_bp.route("/career/<course_name>")
@login_required
def career_detail(course_name: str):
    roadmap = rec_svc.get_career_roadmap(course_name)
    return render_template("careers/roadmap.html", roadmap=roadmap, course_name=course_name)
