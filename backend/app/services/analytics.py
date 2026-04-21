from datetime import datetime, timedelta

from sqlalchemy import desc, extract, func, select
from sqlalchemy.orm import Session

from app.models import Analysis, Facility, OccupancyLog, Upload
from app.schemas.analytics import DailyTrendPoint, FacilityMetric, PeakHourMetric, RecentActivity


def _round(value: float | None) -> float:
    return round(float(value or 0), 4)


def busiest_facilities(db: Session, limit: int = 5) -> list[FacilityMetric]:
    rows = db.execute(
        select(
            Facility.id,
            Facility.name,
            func.avg(OccupancyLog.occupancy_rate),
            func.avg(OccupancyLog.congestion_score),
            func.count(OccupancyLog.id),
        )
        .join(OccupancyLog, OccupancyLog.facility_id == Facility.id)
        .group_by(Facility.id)
        .order_by(desc(func.avg(OccupancyLog.occupancy_rate)))
        .limit(limit)
    ).all()
    metrics: list[FacilityMetric] = []
    for facility_id, name, avg_occ, avg_score, count in rows:
        latest_level = db.scalar(
            select(OccupancyLog.congestion_level)
            .where(OccupancyLog.facility_id == facility_id)
            .order_by(desc(OccupancyLog.timestamp))
            .limit(1)
        )
        metrics.append(
            FacilityMetric(
                facility_id=facility_id,
                facility_name=name,
                average_occupancy_rate=_round(avg_occ),
                average_congestion_score=_round(avg_score),
                latest_congestion_level=latest_level,
                analyses_count=count,
            )
        )
    return metrics


def peak_hours(db: Session, facility_id: int | None = None, days: int = 14) -> list[PeakHourMetric]:
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(
            extract("hour", OccupancyLog.timestamp).label("hour"),
            func.avg(OccupancyLog.occupancy_rate),
            func.avg(OccupancyLog.congestion_score),
            func.count(OccupancyLog.id),
        )
        .where(OccupancyLog.timestamp >= since)
        .group_by("hour")
        .order_by("hour")
    )
    if facility_id:
        stmt = stmt.where(OccupancyLog.facility_id == facility_id)
    return [
        PeakHourMetric(hour=int(hour), average_occupancy_rate=_round(avg_occ), average_congestion_score=_round(avg_score), samples=count)
        for hour, avg_occ, avg_score, count in db.execute(stmt).all()
    ]


def daily_trend(db: Session, facility_id: int, days: int = 14) -> list[DailyTrendPoint]:
    since = datetime.utcnow() - timedelta(days=days)
    day_expr = func.date(OccupancyLog.timestamp)
    rows = db.execute(
        select(day_expr, func.avg(OccupancyLog.occupancy_rate), func.avg(OccupancyLog.congestion_score), func.count(OccupancyLog.id))
        .where(OccupancyLog.facility_id == facility_id, OccupancyLog.timestamp >= since)
        .group_by(day_expr)
        .order_by(day_expr)
    ).all()
    return [
        DailyTrendPoint(date=str(day), average_occupancy_rate=_round(avg_occ), average_congestion_score=_round(avg_score), samples=count)
        for day, avg_occ, avg_score, count in rows
    ]


def recent_activity(db: Session, facility_id: int | None = None, limit: int = 10) -> list[RecentActivity]:
    stmt = (
        select(Analysis.id, Facility.id, Facility.name, Analysis.people_count, Analysis.occupancy_rate, Analysis.congestion_level, Analysis.created_at)
        .join(Facility, Facility.id == Analysis.facility_id)
        .order_by(desc(Analysis.created_at))
        .limit(limit)
    )
    if facility_id:
        stmt = stmt.where(Analysis.facility_id == facility_id)
    return [
        RecentActivity(
            analysis_id=analysis_id,
            facility_id=fac_id,
            facility_name=name,
            people_count=people_count,
            occupancy_rate=occupancy_rate,
            congestion_level=level,
            created_at=created_at,
        )
        for analysis_id, fac_id, name, people_count, occupancy_rate, level, created_at in db.execute(stmt).all()
    ]


def overview_stats(db: Session) -> dict:
    return {
        "facilities_count": db.scalar(select(func.count(Facility.id))) or 0,
        "analyses_count": db.scalar(select(func.count(Analysis.id))) or 0,
        "uploads_count": db.scalar(select(func.count(Upload.id))) or 0,
        "average_occupancy_rate": _round(db.scalar(select(func.avg(OccupancyLog.occupancy_rate)))),
        "average_congestion_score": _round(db.scalar(select(func.avg(OccupancyLog.congestion_score)))),
    }

