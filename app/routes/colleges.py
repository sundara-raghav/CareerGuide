"""Colleges blueprint — map view, search API, detail pages."""

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models.college import College
from app.repositories.college_repo import CollegeRepository

colleges_bp = Blueprint("colleges", __name__, template_folder="../templates/colleges")
college_repo = CollegeRepository()


@colleges_bp.route("/map")
@login_required
def map_view():
    student = current_user.student_profile
    lat = student.latitude if student and student.latitude else 11.0168
    lng = student.longitude if student and student.longitude else 76.9558
    radius = student.travel_radius_km if student else 50.0

    nearby = college_repo.get_nearby(lat, lng, radius_km=radius)
    colleges_json = [c.to_dict(include_distance=d) for c, d in nearby]

    return render_template(
        "colleges/map.html",
        colleges=colleges_json,
        center_lat=lat,
        center_lng=lng,
        radius=radius,
        student=student,
    )


@colleges_bp.route("/api/search")
@login_required
def search():
    district = request.args.get("district")
    college_type = request.args.get("type")
    has_hostel = request.args.get("hostel") == "true"
    max_fees = request.args.get("max_fees", type=float)
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", type=float, default=50.0)

    if lat and lng:
        results = college_repo.get_nearby(lat, lng, radius_km=radius)
        data = [c.to_dict(include_distance=d) for c, d in results]
    else:
        results = college_repo.search(
            district=district,
            college_type=college_type,
            has_hostel=has_hostel if request.args.get("hostel") else None,
            max_fees=max_fees,
        )
        data = [c.to_dict() for c in results]

    return jsonify({"colleges": data, "count": len(data)})


@colleges_bp.route("/<int:college_id>")
@login_required
def detail(college_id: int):
    college = college_repo.get_by_id(college_id)
    if not college:
        return render_template("errors/404.html"), 404
    return render_template("colleges/detail.html", college=college)


@colleges_bp.route("/api/all-pins")
def all_pins():
    """Public endpoint for Google Maps pins — minimal data."""
    colleges = db.session.query(College).filter_by(is_active=True).all()
    pins = [
        {
            "id": c.id,
            "name": c.name,
            "lat": c.latitude,
            "lng": c.longitude,
            "type": c.college_type,
        }
        for c in colleges
        if c.latitude and c.longitude
    ]
    return jsonify(pins)
