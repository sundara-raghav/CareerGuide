"""Generic base repository providing common CRUD operations."""
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extensions import db

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic repository for SQLAlchemy models.
    Subclass and set `model_class` to get full CRUD for free.
    """

    model_class: type[T]

    def __init__(self, session: Session | None = None) -> None:
        self.session: Session = session or db.session

    def get_by_id(self, record_id: int) -> T | None:
        return self.session.get(self.model_class, record_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self.model_class).limit(limit).offset(offset)
        return list(self.session.scalars(stmt))

    def create(self, **kwargs: Any) -> T:
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, record_id: int, **kwargs: Any) -> T | None:
        instance = self.get_by_id(record_id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete(self, record_id: int) -> bool:
        instance = self.get_by_id(record_id)
        if not instance:
            return False
        self.session.delete(instance)
        self.session.flush()
        return True

    def count(self) -> int:
        from sqlalchemy import func
        return self.session.scalar(select(func.count()).select_from(self.model_class)) or 0

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
