from datetime import datetime

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.models import OccupancyLog
from app.schemas.operations import FacilitySummaryRead, LatestStatusRead, OccupancyLogRead
from app.services.storage import public_url_for_path

def normalize_occupancy_source_type(source_type: str | None) -> str:
    normalized = (source_type or "").strip().lower()
    aliases = {
        "upload": "image_upload",
        "image": "image_upload",
        "image_upload": "image_upload",
        "live": "webcam",
        "webcam": "webcam",
        "camera": "webcam",
        "simulator": "simulator",
        "seed": "simulator",
        "demo_scenario": "demo_scenario",
    }
    return aliases.get(normalized, "image_upload")


def create_occupancy_log(
    db: Session,
    *,
    facility_id: int,
    timestamp: datetime,
    people_count: int,
    occupied_seats: int,
    available_seats: int,
    occupancy_rate: float,
    congestion_score: float,
    congestion_level: str,
    analysis_id: int | None = None,
    confidence: float | None = None,
    source_type: str = "image_upload",
    image_path: str | None = None,
    annotated_image_path: str | None = None,
) -> OccupancyLog:
    log = OccupancyLog(
        facility_id=facility_id,
        analysis_id=analysis_id,
        timestamp=timestamp,
        people_count=people_count,
        occupied_seats=occupied_seats,
        available_seats=available_seats,
        occupancy_rate=occupancy_rate,
        congestion_score=congestion_score,
        congestion_level=congestion_level,
        confidence=confidence,
        source_type=normalize_occupancy_source_type(source_type),
        image_path=image_path,
        annotated_image_path=annotated_image_path,
    )
    db.add(log)
    db.flush()
    return log


def serialize_occupancy_log(log: OccupancyLog) -> OccupancyLogRead:
    return OccupancyLogRead(
        id=log.id,
        facility_id=log.facility_id,
        analysis_id=log.analysis_id,
        timestamp=log.timestamp,
        people_count=log.people_count,
        occupied_seats=log.occupied_seats,
        available_seats=log.available_seats,
        occupancy_rate=log.occupancy_rate,
        congestion_score=log.congestion_score,
        congestion_level=log.congestion_level,
        confidence=log.confidence,
        source_type=log.source_type,
        image_path=log.image_path,
        annotated_image_path=log.annotated_image_path,
        image_url=public_url_for_path(log.image_path),
        annotated_image_url=public_url_for_path(log.annotated_image_path),
        created_at=log.created_at,
    )


def list_occupancy_logs(db: Session, facility_id: int, limit: int = 200) -> list[OccupancyLog]:
    return list(
        db.scalars(
            select(OccupancyLog)
            .where(OccupancyLog.facility_id == facility_id)
            .order_by(desc(OccupancyLog.timestamp))
            .limit(limit)
        ).all()
    )


def latest_occupancy_log(db: Session, facility_id: int) -> OccupancyLog | None:
    return db.scalar(
        select(OccupancyLog)
        .where(OccupancyLog.facility_id == facility_id)
        .order_by(desc(OccupancyLog.timestamp))
        .limit(1)
    )


def latest_status(db: Session, facility_id: int) -> LatestStatusRead:
    latest = latest_occupancy_log(db, facility_id)
    if not latest:
        return LatestStatusRead(facility_id=facility_id)

    return LatestStatusRead(
        facility_id=facility_id,
        timestamp=latest.timestamp,
        people_count=latest.people_count,
        occupied_seats=latest.occupied_seats,
        available_seats=latest.available_seats,
        occupancy_rate=latest.occupancy_rate,
        congestion_score=latest.congestion_score,
        congestion_level=latest.congestion_level,
        confidence=latest.confidence,
        source_type=latest.source_type,
        analysis_id=latest.analysis_id,
        image_url=public_url_for_path(latest.image_path),
        annotated_image_url=public_url_for_path(latest.annotated_image_path),
    )


def facility_summary(db: Session, facility_id: int) -> FacilitySummaryRead:
    latest = latest_occupancy_log(db, facility_id)
    aggregates = db.execute(
        select(
            func.avg(OccupancyLog.occupancy_rate),
            func.max(OccupancyLog.occupancy_rate),
            func.count(OccupancyLog.id),
            func.sum(case((OccupancyLog.congestion_level == "High", 1), else_=0)),
            func.max(OccupancyLog.timestamp),
        ).where(OccupancyLog.facility_id == facility_id)
    ).one()

    avg_rate, peak_rate, samples, high_events, recent_timestamp = aggregates
    return FacilitySummaryRead(
        facility_id=facility_id,
        latest_occupancy_rate=latest.occupancy_rate if latest else 0,
        average_occupancy_rate=round(float(avg_rate or 0), 4),
        peak_occupancy_rate=round(float(peak_rate or 0), 4),
        high_congestion_events=int(high_events or 0),
        most_recent_timestamp=recent_timestamp,
        latest_people_count=latest.people_count if latest else 0,
        samples=int(samples or 0),
    )
