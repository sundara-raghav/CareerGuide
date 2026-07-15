"""Student-specific repository queries."""

from sqlalchemy import select

from app.models.student import Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    model_class = Student

    def get_by_user_id(self, user_id: int) -> Student | None:
        stmt = select(Student).where(Student.user_id == user_id)
        return self.session.scalar(stmt)

    def get_by_district(self, district: str, state: str | None = None) -> list[Student]:
        stmt = select(Student).where(Student.district == district)
        if state:
            stmt = stmt.where(Student.state == state)
        return list(self.session.scalars(stmt))

    def get_incomplete_onboarding(self) -> list[Student]:
        stmt = select(Student).where(Student.onboarding_complete.is_(False))
        return list(self.session.scalars(stmt))

    def get_students_needing_reminder(self) -> list[Student]:
        """Students who completed onboarding but haven't taken the quiz."""
        stmt = select(Student).where(
            Student.onboarding_complete.is_(True),
            Student.quiz_complete.is_(False),
        )
        return list(self.session.scalars(stmt))

    def count_by_district(self) -> list[dict]:
        from sqlalchemy import func

        stmt = (
            select(Student.district, Student.state, func.count().label("count"))
            .group_by(Student.district, Student.state)
            .order_by(func.count().desc())
        )
        rows = self.session.execute(stmt).all()
        return [{"district": r.district, "state": r.state, "count": r.count} for r in rows]
