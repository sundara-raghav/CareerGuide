"""Models package — imports all models so SQLAlchemy can register them."""
from app.models.college import College, Scholarship
from app.models.notification import Notification
from app.models.quiz import AptitudeScore, QuizAttempt
from app.models.recommendation import CounselorFeedback, ModelFeedback, Recommendation
from app.models.student import AdmissionEvent, Parent, Student
from app.models.user import User, UserRole

__all__ = [
    "User",
    "UserRole",
    "Student",
    "Parent",
    "AdmissionEvent",
    "QuizAttempt",
    "AptitudeScore",
    "Recommendation",
    "ModelFeedback",
    "CounselorFeedback",
    "College",
    "Scholarship",
    "Notification",
]
