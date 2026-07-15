"""Quiz service — processes quiz responses and computes aptitude scores."""
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.extensions import db
from app.models.quiz import AptitudeScore, QuizAttempt
from app.models.student import Student

log = structlog.get_logger(__name__)

# ── Quiz question bank ─────────────────────────────────────────────────────────
# Each question: {id, section, text, options: [{key, text}], correct_key, weight}
QUESTION_BANK: list[dict] = [
    # LOGICAL (10 questions)
    {"id": 1, "section": "logical", "text": "If all roses are flowers and some flowers fade quickly, which is definitely true?", "options": [{"key": "A", "text": "All roses fade quickly"}, {"key": "B", "text": "Some roses may fade quickly"}, {"key": "C", "text": "No roses fade quickly"}, {"key": "D", "text": "All flowers are roses"}], "correct_key": "B", "weight": 1},
    {"id": 2, "section": "logical", "text": "Find the next number: 2, 6, 12, 20, 30, ?", "options": [{"key": "A", "text": "36"}, {"key": "B", "text": "40"}, {"key": "C", "text": "42"}, {"key": "D", "text": "44"}], "correct_key": "C", "weight": 1},
    {"id": 3, "section": "logical", "text": "Which shape completes the pattern: Circle, Triangle, Square, Circle, Triangle, ?", "options": [{"key": "A", "text": "Circle"}, {"key": "B", "text": "Triangle"}, {"key": "C", "text": "Square"}, {"key": "D", "text": "Pentagon"}], "correct_key": "C", "weight": 1},
    # VERBAL (10 questions)
    {"id": 11, "section": "verbal", "text": "Choose the word most similar in meaning to 'Benevolent':", "options": [{"key": "A", "text": "Cruel"}, {"key": "B", "text": "Kind"}, {"key": "C", "text": "Lazy"}, {"key": "D", "text": "Clever"}], "correct_key": "B", "weight": 1},
    {"id": 12, "section": "verbal", "text": "Fill in the blank: She was _____ praised for her courage.", "options": [{"key": "A", "text": "harshly"}, {"key": "B", "text": "rarely"}, {"key": "C", "text": "widely"}, {"key": "D", "text": "poorly"}], "correct_key": "C", "weight": 1},
    # QUANTITATIVE (10 questions)
    {"id": 21, "section": "quantitative", "text": "A train travels 360 km in 4 hours. What is its speed in km/h?", "options": [{"key": "A", "text": "80"}, {"key": "B", "text": "90"}, {"key": "C", "text": "100"}, {"key": "D", "text": "120"}], "correct_key": "B", "weight": 1},
    {"id": 22, "section": "quantitative", "text": "What is 15% of 240?", "options": [{"key": "A", "text": "32"}, {"key": "B", "text": "36"}, {"key": "C", "text": "38"}, {"key": "D", "text": "40"}], "correct_key": "B", "weight": 1},
    {"id": 23, "section": "quantitative", "text": "If x + y = 10 and x - y = 4, what is x?", "options": [{"key": "A", "text": "5"}, {"key": "B", "text": "6"}, {"key": "C", "text": "7"}, {"key": "D", "text": "8"}], "correct_key": "C", "weight": 1},
    # SOCIAL (8 questions)
    {"id": 31, "section": "social", "text": "You see a classmate struggling with an assignment. You would:", "options": [{"key": "A", "text": "Ignore — it's their problem"}, {"key": "B", "text": "Offer to help and explain"}, {"key": "C", "text": "Tell the teacher"}, {"key": "D", "text": "Do it for them"}], "correct_key": "B", "weight": 1},
    {"id": 32, "section": "social", "text": "In a group project conflict, you would:", "options": [{"key": "A", "text": "Dominate and impose your view"}, {"key": "B", "text": "Quit the group"}, {"key": "C", "text": "Facilitate a discussion and find middle ground"}, {"key": "D", "text": "Let others decide everything"}], "correct_key": "C", "weight": 1},
    # CREATIVE (8 questions)
    {"id": 41, "section": "creative", "text": "How many uses can you think of for a brick? This question tests:", "options": [{"key": "A", "text": "Memory"}, {"key": "B", "text": "Divergent thinking"}, {"key": "C", "text": "Mathematical reasoning"}, {"key": "D", "text": "Vocabulary"}], "correct_key": "B", "weight": 1},
    {"id": 42, "section": "creative", "text": "You love drawing posters and making short films. This suggests aptitude for:", "options": [{"key": "A", "text": "Accounting"}, {"key": "B", "text": "Law"}, {"key": "C", "text": "Visual arts and media"}, {"key": "D", "text": "Chemistry"}], "correct_key": "C", "weight": 1},
    # TECHNICAL (10 questions)
    {"id": 51, "section": "technical", "text": "Which component stores data permanently in a computer?", "options": [{"key": "A", "text": "RAM"}, {"key": "B", "text": "CPU"}, {"key": "C", "text": "Hard Disk"}, {"key": "D", "text": "GPU"}], "correct_key": "C", "weight": 1},
    {"id": 52, "section": "technical", "text": "Ohm's law states that V = ?", "options": [{"key": "A", "text": "I / R"}, {"key": "B", "text": "I × R"}, {"key": "C", "text": "R / I"}, {"key": "D", "text": "I + R"}], "correct_key": "B", "weight": 1},
    {"id": 53, "section": "technical", "text": "Which programming concept allows code reuse?", "options": [{"key": "A", "text": "Variable"}, {"key": "B", "text": "Loop"}, {"key": "C", "text": "Function"}, {"key": "D", "text": "Comment"}], "correct_key": "C", "weight": 1},
]

SECTIONS = ["logical", "verbal", "quantitative", "social", "creative", "technical"]
SECTION_MAX: dict[str, int] = {
    "logical": 3, "verbal": 2, "quantitative": 3, "social": 2, "creative": 2, "technical": 3,
}


class QuizService:
    def get_questions(self) -> list[dict]:
        return QUESTION_BANK

    def get_sections(self) -> list[str]:
        return SECTIONS

    def start_attempt(self, student_id: int) -> QuizAttempt:
        attempt = QuizAttempt(student_id=student_id)
        db.session.add(attempt)
        db.session.commit()
        return attempt

    def submit_attempt(self, attempt_id: int, responses: list[dict]) -> AptitudeScore:
        """
        responses: [{question_id: int, selected_key: str}]
        Scores each section, normalizes to 0–100, saves AptitudeScore.
        """
        attempt = db.session.get(QuizAttempt, attempt_id)
        if not attempt:
            raise ValueError(f"QuizAttempt {attempt_id} not found")

        attempt.responses = responses
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.is_complete = True

        # Handle naive/aware datetime differences (e.g. SQLite doesn't preserve tzinfo)
        started = attempt.started_at
        completed = attempt.completed_at
        if started.tzinfo is None and completed.tzinfo is not None:
            completed = completed.replace(tzinfo=None)
        elif started.tzinfo is not None and completed.tzinfo is None:
            started = started.replace(tzinfo=None)

        attempt.time_taken_seconds = int((completed - started).total_seconds())

        scores = self._score_responses(responses)

        # Check if AptitudeScore already exists (re-attempt)
        existing = db.session.query(AptitudeScore).filter_by(student_id=attempt.student_id).first()
        if existing:
            db.session.delete(existing)
            db.session.flush()

        apt = AptitudeScore(
            student_id=attempt.student_id,
            quiz_attempt_id=attempt_id,
            **scores,
        )
        apt.composite = round(sum(scores.values()) / len(scores), 2)

        db.session.add(apt)

        # Update student quiz status
        student = db.session.get(Student, attempt.student_id)
        if student:
            student.quiz_complete = True

        db.session.commit()
        log.info("Quiz submitted", student_id=attempt.student_id, composite=apt.composite)
        return apt

    def _score_responses(self, responses: list[dict]) -> dict[str, float]:
        """Returns normalized scores (0–100) per section."""
        q_map = {q["id"]: q for q in QUESTION_BANK}
        section_correct: dict[str, int] = {s: 0 for s in SECTIONS}
        section_total: dict[str, int] = {s: 0 for s in SECTIONS}

        for resp in responses:
            q = q_map.get(resp.get("question_id"))
            if not q:
                continue
            section = q["section"]
            section_total[section] = section_total.get(section, 0) + 1
            if resp.get("selected_key") == q["correct_key"]:
                section_correct[section] = section_correct.get(section, 0) + 1

        normalized: dict[str, float] = {}
        for section in SECTIONS:
            total = max(section_total.get(section, 1), 1)
            correct = section_correct.get(section, 0)
            normalized[section] = round((correct / total) * 100, 2)

        return normalized
