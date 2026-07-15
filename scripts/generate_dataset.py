"""
Synthetic student dataset generator for training the recommendation engine.

Generates ~1000+ realistic student profiles with labels covering:
- stream (Science / Commerce / Arts / Vocational)
- top_course (20 course categories)
- career_cluster (10 clusters)

Run: python scripts/generate_dataset.py
Output: data/synthetic_students.csv
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

# ─── Constants ────────────────────────────────────────────────────────────────

STREAMS = ["Science", "Commerce", "Arts", "Vocational"]

STREAM_COURSES: dict[str, list[str]] = {
    "Science": [
        "BTech/BE",
        "BSc Physics",
        "BSc Chemistry",
        "BSc Biology",
        "BSc Math",
        "MBBS/BDS",
        "Pharmacy (BPharm)",
        "Nursing (BSc)",
        "BCA",
        "BSc Agriculture",
    ],
    "Commerce": [
        "BCom",
        "BBA",
        "CA Foundation",
        "BBA Finance",
        "BBA Marketing",
        "BCom Computer Apps",
        "Hotel Management",
        "BMS",
    ],
    "Arts": [
        "BA English",
        "BA History",
        "BA Psychology",
        "BA Political Science",
        "BA Social Work",
        "BFA",
        "BJournalism",
        "BA Economics",
    ],
    "Vocational": [
        "Diploma Engineering",
        "ITI Electrician",
        "ITI Fitter",
        "ITI Mechanic",
        "Polytechnic",
        "Animation Diploma",
        "Fashion Design Diploma",
        "Paramedical Diploma",
    ],
}

CAREER_CLUSTERS = [
    "Engineering & Technology",
    "Healthcare & Medicine",
    "Business & Finance",
    "Education & Social Work",
    "Arts & Media",
    "Government & Civil Services",
    "Agriculture & Environment",
    "Trades & Skilled Work",
    "Law & Public Policy",
    "Science & Research",
]

BOARDS = ["CBSE", "State Board", "ICSE", "Matriculation"]
DISTRICTS = [
    "Chennai",
    "Coimbatore",
    "Madurai",
    "Trichy",
    "Salem",
    "Tirunelveli",
    "Erode",
    "Vellore",
    "Thanjavur",
    "Kanchipuram",
    "Villupuram",
    "Dharmapuri",
    "Namakkal",
    "Karur",
    "Dindigul",
    "Ariyalur",
    "Perambalur",
    "Cuddalore",
]
INTERESTS_POOL = [
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
SCHOOL_TYPES = ["government", "private", "aided"]


def _generate_marks(student_class: int, stream_hint: str) -> dict:
    """Generate subject-wise marks with stream-appropriate biases."""
    base = random.gauss(65, 15)
    base = max(25, min(100, base))

    subjects_10 = {
        "math": base + random.gauss(5 if stream_hint in ["Science", "Vocational"] else -5, 8),
        "science": base + random.gauss(5 if stream_hint == "Science" else -3, 8),
        "social": base + random.gauss(5 if stream_hint == "Arts" else -2, 8),
        "english": base + random.gauss(0, 6),
        "regional_language": base + random.gauss(0, 6),
    }
    subjects_12 = {
        "english": base + random.gauss(0, 6),
        "core_subject_1": base + random.gauss(8 if stream_hint in ["Science", "Commerce"] else 0, 10),
        "core_subject_2": base + random.gauss(5, 8),
        "elective_1": base + random.gauss(3, 8),
        "elective_2": base + random.gauss(2, 8),
    }
    raw = subjects_10 if student_class == 10 else subjects_12
    return {k: round(max(0, min(100, v)), 1) for k, v in raw.items()}


def _aptitude_profile(stream: str) -> dict:
    """Generate aptitude scores consistent with the target stream."""
    profiles = {
        "Science": dict(logical=70, verbal=55, quantitative=75, social=50, creative=55, technical=80),
        "Commerce": dict(logical=65, verbal=65, quantitative=72, social=65, creative=50, technical=45),
        "Arts": dict(logical=55, verbal=80, quantitative=45, social=75, creative=80, technical=40),
        "Vocational": dict(logical=60, verbal=55, quantitative=58, social=60, creative=65, technical=75),
    }
    base = profiles[stream]

    def noise(v):
        return round(max(0, min(100, v + random.gauss(0, 10))), 1)

    return {k: noise(v) for k, v in base.items()}


def _label_course(stream: str) -> str:
    return random.choice(STREAM_COURSES[stream])


def _label_career(stream: str, course: str) -> str:
    mapping = {
        "BTech/BE": "Engineering & Technology",
        "BCA": "Engineering & Technology",
        "BSc Physics": "Science & Research",
        "BSc Chemistry": "Science & Research",
        "BSc Math": "Science & Research",
        "BSc Biology": "Healthcare & Medicine",
        "MBBS/BDS": "Healthcare & Medicine",
        "Nursing (BSc)": "Healthcare & Medicine",
        "Pharmacy (BPharm)": "Healthcare & Medicine",
        "BSc Agriculture": "Agriculture & Environment",
        "BCom": "Business & Finance",
        "BBA": "Business & Finance",
        "CA Foundation": "Business & Finance",
        "BBA Finance": "Business & Finance",
        "BBA Marketing": "Business & Finance",
        "BCom Computer Apps": "Engineering & Technology",
        "Hotel Management": "Business & Finance",
        "BMS": "Business & Finance",
        "BA English": "Arts & Media",
        "BA History": "Education & Social Work",
        "BA Psychology": "Education & Social Work",
        "BA Political Science": "Government & Civil Services",
        "BA Social Work": "Education & Social Work",
        "BFA": "Arts & Media",
        "BJournalism": "Arts & Media",
        "BA Economics": "Business & Finance",
        "Diploma Engineering": "Trades & Skilled Work",
        "ITI Electrician": "Trades & Skilled Work",
        "ITI Fitter": "Trades & Skilled Work",
        "ITI Mechanic": "Trades & Skilled Work",
        "Polytechnic": "Trades & Skilled Work",
        "Animation Diploma": "Arts & Media",
        "Fashion Design Diploma": "Arts & Media",
        "Paramedical Diploma": "Healthcare & Medicine",
    }
    return mapping.get(course, "Government & Civil Services")


def generate_dataset(n: int = 1200) -> pd.DataFrame:
    records = []
    for i in range(n):
        student_class = random.choice([10, 12])
        stream = random.choices(STREAMS, weights=[0.40, 0.30, 0.20, 0.10])[0]
        marks = _generate_marks(student_class, stream)
        aggregate = round(np.mean(list(marks.values())), 1)
        aptitude = _aptitude_profile(stream)
        course = _label_course(stream)
        career = _label_career(stream, course)

        n_interests = random.randint(2, 5)
        interests = random.sample(INTERESTS_POOL, n_interests)

        record = {
            "student_id": i + 1,
            "student_class": student_class,
            "board": random.choice(BOARDS),
            "school_type": random.choices(SCHOOL_TYPES, weights=[0.55, 0.30, 0.15])[0],
            "district": random.choice(DISTRICTS),
            "aggregate_percentage": aggregate,
            "annual_family_income": round(np.random.lognormal(11.0, 0.8)),
            "budget_for_education": round(random.uniform(10000, 300000)),
            "travel_radius_km": random.choice([10, 20, 30, 50, 75, 100]),
            "needs_hostel": random.random() < 0.35,
            "needs_scholarship": random.random() < 0.60,
            "gender": random.choice(["Male", "Female", "Other"]),
            "caste_category": random.choices(["General", "OBC", "SC", "ST"], weights=[0.30, 0.40, 0.20, 0.10])[0],
            # Marks
            **{f"mark_{k}": v for k, v in marks.items()},
            # Aptitude
            **{f"apt_{k}": v for k, v in aptitude.items()},
            # Interests as binary flags
            **{f"interest_{interest}": (interest in interests) for interest in INTERESTS_POOL},
            # Labels
            "target_stream": stream,
            "target_course": course,
            "target_career_cluster": career,
        }
        records.append(record)

    df = pd.DataFrame(records)
    return df


def main() -> None:
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    df = generate_dataset(1200)
    out_path = out_dir / "synthetic_students.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} student records to {out_path}")
    print(f"Stream distribution:\n{df['target_stream'].value_counts()}")
    print(f"Career cluster distribution:\n{df['target_career_cluster'].value_counts()}")


if __name__ == "__main__":
    main()
