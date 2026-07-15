"""College repository with geospatial queries."""

import math

from sqlalchemy import and_, or_, select

from app.models.college import College
from app.repositories.base import BaseRepository


class CollegeRepository(BaseRepository[College]):
    model_class = College

    def get_by_slug(self, slug: str) -> College | None:
        return self.session.scalar(select(College).where(College.slug == slug))

    def search(
        self,
        district: str | None = None,
        state: str | None = None,
        college_type: str | None = None,
        has_hostel: bool | None = None,
        max_fees: float | None = None,
        course_name: str | None = None,
        limit: int = 50,
    ) -> list[College]:
        stmt = select(College).where(College.is_active.is_(True))
        if district:
            stmt = stmt.where(College.district.ilike(f"%{district}%"))
        if state:
            stmt = stmt.where(College.state == state)
        if college_type:
            stmt = stmt.where(College.college_type == college_type)
        if has_hostel is not None:
            stmt = stmt.where(College.has_hostel == has_hostel)
        if max_fees:
            stmt = stmt.where(or_(College.annual_fees_min <= max_fees, College.annual_fees_min.is_(None)))
        return list(self.session.scalars(stmt.limit(limit)))

    def get_nearby(
        self,
        lat: float,
        lng: float,
        radius_km: float = 50.0,
        limit: int = 30,
    ) -> list[tuple[College, float]]:
        """
        Haversine-approximate filter: fetches colleges within a bounding box,
        then computes exact distance in Python.
        For large datasets, move this to PostGIS or a spatial index.
        """
        deg_lat = radius_km / 111.0
        deg_lng = radius_km / (111.0 * math.cos(math.radians(lat)))

        stmt = select(College).where(
            and_(
                College.is_active.is_(True),
                College.latitude.between(lat - deg_lat, lat + deg_lat),
                College.longitude.between(lng - deg_lng, lng + deg_lng),
            )
        )
        candidates = list(self.session.scalars(stmt))

        results: list[tuple[College, float]] = []
        for college in candidates:
            if college.latitude and college.longitude:
                dist = _haversine(lat, lng, college.latitude, college.longitude)
                if dist <= radius_km:
                    results.append((college, dist))

        results.sort(key=lambda x: x[1])
        return results[:limit]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in km between two lat/lng points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))
