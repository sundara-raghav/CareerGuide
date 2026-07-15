"""Recommendation repository."""

from sqlalchemy import desc, select

from app.models.recommendation import ModelFeedback, Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    model_class = Recommendation

    def get_latest_for_student(self, student_id: int) -> Recommendation | None:
        stmt = (
            select(Recommendation)
            .where(Recommendation.student_id == student_id)
            .order_by(desc(Recommendation.created_at))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_all_for_student(self, student_id: int) -> list[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(Recommendation.student_id == student_id)
            .order_by(desc(Recommendation.created_at))
        )
        return list(self.session.scalars(stmt))

    def get_acceptance_rate(self) -> float:
        """Returns the fraction of recommendations that were accepted."""
        from sqlalchemy import func

        total = self.session.scalar(
            select(func.count()).select_from(ModelFeedback).where(ModelFeedback.accepted.isnot(None))
        )
        accepted = self.session.scalar(
            select(func.count()).select_from(ModelFeedback).where(ModelFeedback.accepted.is_(True))
        )
        if not total:
            return 0.0
        return round((accepted or 0) / total, 4)

    def get_stream_distribution(self) -> list[dict]:
        from sqlalchemy import func

        stmt = select(Recommendation.recommended_stream, func.count().label("count")).group_by(
            Recommendation.recommended_stream
        )
        rows = self.session.execute(stmt).all()
        return [{"stream": r.recommended_stream, "count": r.count} for r in rows]
