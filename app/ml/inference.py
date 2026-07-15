"""
Flask-integrated inference service.

Usage (from Flask route):
    from app.ml.inference import get_recommendation

    result = get_recommendation(student, aptitude_score)
    # result = {stream, courses, careers, explanations, scholarship_matches}
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from app.models.quiz import AptitudeScore
    from app.models.student import Student

_ARTIFACTS_DIR = Path(os.getenv("ML_ARTIFACTS_DIR", "app/ml/artifacts"))
_ENSEMBLE_PATH = _ARTIFACTS_DIR / "ensemble.pkl"
_PIPELINE_PATH = _ARTIFACTS_DIR / "preprocessing_pipeline.pkl"


@lru_cache(maxsize=1)
def _load_ensemble():
    """Load and cache ensemble — called once per worker process."""
    if not _ENSEMBLE_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found at {_ENSEMBLE_PATH}. " "Run: python scripts/train_model.py")
    return joblib.load(_ENSEMBLE_PATH)


@lru_cache(maxsize=1)
def _load_pipeline():
    if not _PIPELINE_PATH.exists():
        raise FileNotFoundError(f"Pipeline artifact not found at {_PIPELINE_PATH}.")
    return joblib.load(_PIPELINE_PATH)


def _student_to_dataframe(student: Student, aptitude: AptitudeScore) -> pd.DataFrame:
    """Convert ORM objects to a one-row DataFrame matching training features."""
    marks = student.marks or {}

    row: dict = {
        "student_class": student.student_class,
        "board": student.board or "State Board",
        "school_type": student.school_type or "government",
        "district": student.district or "",
        "aggregate_percentage": student.aggregate_percentage or 0.0,
        "annual_family_income": student.annual_family_income or 0.0,
        "budget_for_education": student.budget_for_education or 0.0,
        "travel_radius_km": student.travel_radius_km or 50.0,
        "needs_hostel": int(student.needs_hostel or False),
        "needs_scholarship": int(student.needs_scholarship or False),
        "gender": "Unknown",
        "caste_category": "General",
        # Mark columns
        "mark_math": marks.get("math", marks.get("mark_math", 0)),
        "mark_science": marks.get("science", marks.get("mark_science", 0)),
        "mark_social": marks.get("social", marks.get("mark_social", 0)),
        "mark_english": marks.get("english", marks.get("mark_english", 0)),
        "mark_regional_language": marks.get("regional_language", marks.get("mark_regional_language", 0)),
        "mark_core_subject_1": marks.get("core_subject_1", marks.get("mark_core_subject_1", 0)),
        "mark_core_subject_2": marks.get("core_subject_2", marks.get("mark_core_subject_2", 0)),
        "mark_elective_1": marks.get("elective_1", marks.get("mark_elective_1", 0)),
        "mark_elective_2": marks.get("elective_2", marks.get("mark_elective_2", 0)),
        # Aptitude
        "apt_logical": aptitude.logical,
        "apt_verbal": aptitude.verbal,
        "apt_quantitative": aptitude.quantitative,
        "apt_social": aptitude.social,
        "apt_creative": aptitude.creative,
        "apt_technical": aptitude.technical,
    }

    interests = set(student.interests or [])
    interest_pool = [
        "mathematics",
        "biology",
        "computers",
        "sports",
        "arts",
        "music",
        "social_service",
        "business",
        "nature",
        "writing",
        "politics",
        "cooking",
        "electronics",
        "farming",
        "healthcare",
        "teaching",
    ]
    for interest in interest_pool:
        row[f"interest_{interest}"] = int(interest in interests)

    return pd.DataFrame([row])


def get_recommendation(
    student: Student,
    aptitude: AptitudeScore,
) -> dict:
    """
    Main inference entry point called from recommendation_service.py.
    Returns a structured dict ready to be stored in the Recommendation model.
    """
    ensemble = _load_ensemble()
    pipeline = _load_pipeline()

    df = _student_to_dataframe(student, aptitude)

    # Transform through preprocessing pipeline
    try:
        X = pipeline.transform(df)
    except Exception:
        # If pipeline transform fails (e.g., unseen categories), use zeros
        n_features = len(pipeline.named_steps["col_select"].feature_cols_)
        X = np.zeros((1, n_features))

    context = {
        "budget_for_education": student.budget_for_education,
        "travel_radius_km": student.travel_radius_km,
        "needs_hostel": student.needs_hostel,
    }

    raw = ensemble.predict(X, student_context=context)

    # Build explanation from feature importances
    importances = ensemble.stream_clf.get_feature_importances()
    top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:8]
    explanations = {
        "top_factors": [{"feature": k, "importance": round(v, 4)} for k, v in top_features],
        "aptitude_summary": {
            "logical": aptitude.logical,
            "verbal": aptitude.verbal,
            "quantitative": aptitude.quantitative,
            "social": aptitude.social,
            "creative": aptitude.creative,
            "technical": aptitude.technical,
        },
        "marks_aggregate": student.aggregate_percentage,
    }

    return {
        "recommended_stream": raw["stream"][0]["label"],
        "stream_confidence": raw["stream"][0]["confidence"],
        "top_courses": raw["courses"],
        "career_clusters": raw["careers"],
        "explanations": explanations,
    }


def warmup() -> None:
    """Pre-load models into memory — call at app startup."""
    try:
        _load_ensemble()
        _load_pipeline()
    except FileNotFoundError:
        pass  # Models not trained yet — will fail gracefully at inference time
