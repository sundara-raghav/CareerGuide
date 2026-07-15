"""Repositories package."""

from app.repositories.base import BaseRepository
from app.repositories.college_repo import CollegeRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.student_repo import StudentRepository

__all__ = ["BaseRepository", "StudentRepository", "CollegeRepository", "RecommendationRepository"]
