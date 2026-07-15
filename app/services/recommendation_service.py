"""Recommendation service — orchestrates ML inference + scholarship matching."""

from __future__ import annotations

import structlog

from app.extensions import db
from app.ml.inference import get_recommendation
from app.models.college import Scholarship
from app.models.quiz import AptitudeScore
from app.models.recommendation import Recommendation
from app.models.student import Student
from app.repositories.recommendation_repo import RecommendationRepository

log = structlog.get_logger(__name__)

# ─── Career roadmap data ───────────────────────────────────────────────────────
CAREER_ROADMAPS: dict[str, dict] = {
    "BTech/BE": {
        "competitive_exams": ["JEE Main", "JEE Advanced", "TNEA", "COMEDK", "State CET"],
        "jobs": ["Software Engineer", "Mechanical Engineer", "Civil Engineer", "Data Scientist", "DevOps Engineer"],
        "higher_studies": ["MTech", "MBA", "MS Abroad", "PhD"],
        "entrepreneurial": ["Tech Startup", "Engineering Consultancy", "SaaS Product"],
        "salary_entry": "₹3–8 LPA",
        "salary_senior": "₹15–40 LPA",
        "growth_outlook": "Very High",
    },
    "MBBS/BDS": {
        "competitive_exams": ["NEET UG", "NEET PG", "USMLE (abroad)"],
        "jobs": ["Doctor (General Practice)", "Surgeon", "Dentist", "Medical Officer (Govt)"],
        "higher_studies": ["MD/MS", "MDS", "Superspeciality (DM/MCh)", "MPH"],
        "entrepreneurial": ["Clinic/Hospital", "Health Tech"],
        "salary_entry": "₹5–12 LPA",
        "salary_senior": "₹20–60 LPA",
        "growth_outlook": "Very High",
    },
    "BCom": {
        "competitive_exams": ["CA Foundation", "CMA", "CS", "UPSC", "Bank PO", "SSC CGL"],
        "jobs": ["Accountant", "Financial Analyst", "Tax Consultant", "Auditor", "Bank Clerk"],
        "higher_studies": ["MCom", "MBA Finance", "CA Final", "CFA"],
        "entrepreneurial": ["CA Firm", "Accounting Services", "FinTech"],
        "salary_entry": "₹2–5 LPA",
        "salary_senior": "₹10–25 LPA",
        "growth_outlook": "High",
    },
    "BA English": {
        "competitive_exams": ["UPSC Civil Services", "TN PSC", "NET/SET", "Bank PO", "SSC"],
        "jobs": ["Content Writer", "Teacher", "IAS/IPS Officer", "Journalist", "HR Executive"],
        "higher_studies": ["MA English", "MA Journalism", "MBA", "LLB", "B.Ed"],
        "entrepreneurial": ["Content Agency", "EdTech", "Publishing"],
        "salary_entry": "₹2–4 LPA",
        "salary_senior": "₹8–20 LPA",
        "growth_outlook": "Moderate",
    },
    "ITI Electrician": {
        "competitive_exams": ["TANGEDCO Apprentice", "Railways Technician", "SSC Technical"],
        "jobs": ["Electrician", "Maintenance Technician", "Wireman", "Substation Operator"],
        "higher_studies": ["Diploma (Lateral Entry)", "Apprenticeship", "BTech Lateral"],
        "entrepreneurial": ["Electrical Contracting", "Solar Installation", "AC Service"],
        "salary_entry": "₹1.5–3 LPA",
        "salary_senior": "₹4–10 LPA",
        "growth_outlook": "Steady",
    },
}

DEFAULT_ROADMAP = {
    "competitive_exams": ["UPSC", "State PSC", "SSC CGL", "Railway Exams", "Bank PO"],
    "jobs": ["Government Officer", "Private Sector Professional"],
    "higher_studies": ["Postgraduate Degree", "Professional Certification"],
    "entrepreneurial": ["Small Business", "Freelancing"],
    "salary_entry": "₹2–5 LPA",
    "salary_senior": "₹8–20 LPA",
    "growth_outlook": "Moderate",
}


class RecommendationService:
    def __init__(self) -> None:
        self.repo = RecommendationRepository()

    def generate_for_student(self, student: Student) -> Recommendation | None:
        """
        Full recommendation pipeline:
        1. Check aptitude score exists
        2. Run ML inference
        3. Match scholarships
        4. Persist and return Recommendation
        """
        aptitude = student.aptitude_score
        if not aptitude:
            log.warning("No aptitude score found", student_id=student.id)
            return None

        try:
            ml_result = get_recommendation(student, aptitude)
        except FileNotFoundError:
            log.warning("ML model not trained yet — using rule-based fallback", student_id=student.id)
            ml_result = _rule_based_fallback(student, aptitude)

        scholarships = _match_scholarships(student)

        rec = Recommendation(
            student_id=student.id,
            recommended_stream=ml_result["recommended_stream"],
            stream_confidence=ml_result["stream_confidence"],
            top_courses=ml_result["top_courses"],
            career_clusters=ml_result["career_clusters"],
            explanations=ml_result["explanations"],
            scholarship_matches=scholarships,
        )

        db.session.add(rec)
        db.session.commit()
        log.info("Recommendation generated", student_id=student.id, stream=rec.recommended_stream)
        return rec

    def get_career_roadmap(self, course_name: str) -> dict:
        """Returns structured career roadmap for a given course."""
        for key, roadmap in CAREER_ROADMAPS.items():
            if key.lower() in course_name.lower() or course_name.lower() in key.lower():
                return {"course": course_name, **roadmap}
        return {"course": course_name, **DEFAULT_ROADMAP}

    def record_feedback(
        self,
        recommendation_id: int,
        student_id: int,
        accepted: bool,
        recommended_course: str,
    ) -> None:
        from app.models.recommendation import ModelFeedback

        feedback = ModelFeedback(
            recommendation_id=recommendation_id,
            student_id=student_id,
            accepted=accepted,
            recommended_course=recommended_course,
        )
        db.session.add(feedback)
        db.session.commit()

    def get_recommended_colleges(self, student: Student, recommendation: Recommendation) -> list[dict]:
        """
        Dynamically filters and ranks colleges for a student's recommendations:
        1. Must offer one of the recommended courses
        2. Filter by max budget if budget_for_education is set
        3. Match district or fallback to nearest coordinates
        """
        if not recommendation or not recommendation.top_courses:
            return []

        recommended_course_names = {c["label"].lower() for c in recommendation.top_courses}

        # Load all active colleges
        from app.models.college import College

        colleges = db.session.query(College).filter_by(is_active=True).all()

        matched = []
        for c in colleges:
            # Check if college offers at least one recommended course
            matching_courses = []
            for course_offered in c.courses_offered:
                course_name = course_offered.get("name", "").lower()
                for rec_course in recommended_course_names:
                    if course_name in rec_course or rec_course in course_name:
                        matching_courses.append(course_offered.get("name", ""))
                        break

            if not matching_courses:
                continue

            # Filter by education budget
            if student.budget_for_education and c.annual_fees_min:
                if c.annual_fees_min > student.budget_for_education:
                    continue

            # Compute distance if coordinates available
            distance = None
            if student.latitude and student.longitude and c.latitude and c.longitude:
                from app.repositories.college_repo import _haversine

                distance = _haversine(student.latitude, student.longitude, c.latitude, c.longitude)

            # Compute score/rank based on matching district & distance
            score = 0.0
            if student.district and c.district.lower() == student.district.lower():
                score += 100.0  # Big boost for same district

            if distance is not None:
                # Closer colleges get higher scores (max 50 points)
                score += max(0, 50.0 - (distance / 2.0))

            matched.append({"college": c, "matching_courses": matching_courses, "distance": distance, "score": score})

        # Sort matched colleges by score descending
        matched.sort(key=lambda x: x["score"], reverse=True)

        # Limit to top 5 recommended colleges
        return matched[:5]


def _match_scholarships(student: Student) -> list[dict]:
    """
    Rule-based scholarship eligibility scoring.
    Returns top matching scholarships with score 0–1.
    """
    scholarships = db.session.query(Scholarship).filter_by(is_active=True).all()
    results = []

    for s in scholarships:
        score = _compute_scholarship_score(student, s)
        if score > 0.4:
            results.append(
                {
                    "scholarship_id": s.id,
                    "name": s.name,
                    "provider": s.provider,
                    "amount": s.amount_description or f"₹{s.amount:,.0f}" if s.amount else "Variable",
                    "deadline": s.deadline.isoformat() if s.deadline else None,
                    "application_link": s.application_link,
                    "score": round(score, 3),
                    "eligible": score >= 0.7,
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]


def _compute_scholarship_score(student: Student, scholarship: Scholarship) -> float:
    criteria = scholarship.eligibility_criteria
    score = 1.0

    if "class" in criteria:
        if student.student_class not in criteria["class"]:
            return 0.0

    if "income_max" in criteria:
        income = student.annual_family_income or 999999
        if income > criteria["income_max"]:
            return 0.0
        score *= max(0.5, 1.0 - (income / criteria["income_max"]) * 0.5)

    if "marks_min" in criteria:
        pct = student.aggregate_percentage or 0
        if pct < criteria["marks_min"]:
            score *= 0.3
        else:
            score *= min(1.0, pct / 100 + 0.1)

    if "school_type" in criteria:
        if student.school_type in criteria["school_type"]:
            score *= 1.2

    return min(1.0, score)


def _rule_based_fallback(student: Student, aptitude: AptitudeScore) -> dict:
    """Deterministic fallback when ML model is not available."""
    apt = aptitude

    # Simple rule: highest aptitude domain wins
    scores = {
        "Science": (apt.quantitative + apt.technical + apt.logical) / 3,
        "Commerce": (apt.quantitative + apt.verbal + apt.logical) / 3,
        "Arts": (apt.verbal + apt.social + apt.creative) / 3,
        "Vocational": (apt.technical + apt.creative + apt.logical) / 3,
    }
    stream = max(scores, key=scores.get)  # type: ignore
    conf = round(scores[stream] / 100, 3)

    courses_map = {
        "Science": ["BTech/BE", "BSc Physics", "BSc Biology", "BCA", "Pharmacy (BPharm)"],
        "Commerce": ["BCom", "BBA", "CA Foundation", "BBA Finance", "Hotel Management"],
        "Arts": ["BA English", "BA Psychology", "BA Social Work", "BJournalism", "BA Economics"],
        "Vocational": ["ITI Electrician", "Diploma Engineering", "Polytechnic", "Paramedical Diploma", "ITI Fitter"],
    }
    courses = [
        {"rank": i + 1, "label": c, "confidence": round(conf - i * 0.05, 3)} for i, c in enumerate(courses_map[stream])
    ]

    return {
        "recommended_stream": stream,
        "stream_confidence": conf,
        "top_courses": courses,
        "career_clusters": [{"rank": 1, "label": "Government & Civil Services", "confidence": 0.5}],
        "explanations": {"fallback": True, "rule": f"Highest domain: {stream}"},
    }
