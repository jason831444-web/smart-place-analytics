from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import FacilityOperationalRollup, OccupancyLog, SensorLog
from app.schemas.operations import FacilityOperationalRollupRead
from app.services.recommendations import build_recommendations
from app.utils.time import utc_now

ROLLUP_DEDUP_SECONDS = 300


@dataclass(frozen=True)
class RollupComputation:
    avg_occupancy_rate: float
    peak_occupancy_rate: float
    high_congestion_events: int
    avg_power_kw: float | None
    peak_power_kw: float | None
    avg_temperature: float | None
    avg_noise_level: float | None
    recommendation_count: int


def latest_rollup(db: Session, facility_id: int, window_minutes: int | None = None) -> FacilityOperationalRollup | None:
    stmt = (
        select(FacilityOperationalRollup)
        .where(FacilityOperationalRollup.facility_id == facility_id)
        .order_by(desc(FacilityOperationalRollup.timestamp))
        .limit(1)
    )
    if window_minutes is not None:
        stmt = stmt.where(FacilityOperationalRollup.window_minutes == window_minutes)
    return db.scalar(stmt)


def list_rollups(db: Session, facility_id: int, limit: int = 100) -> list[FacilityOperationalRollup]:
    return list(
        db.scalars(
            select(FacilityOperationalRollup)
            .where(FacilityOperationalRollup.facility_id == facility_id)
            .order_by(desc(FacilityOperationalRollup.timestamp))
            .limit(limit)
        ).all()
    )


def compute_rollup_metrics(db: Session, facility_id: int, window_minutes: int = 60) -> RollupComputation:
    since = utc_now() - timedelta(minutes=window_minutes)

    avg_occupancy_rate, peak_occupancy_rate, high_congestion_events = db.execute(
        select(
            func.avg(OccupancyLog.occupancy_rate),
            func.max(OccupancyLog.occupancy_rate),
            func.count().filter(OccupancyLog.congestion_level == "High"),
        ).where(
            OccupancyLog.facility_id == facility_id,
            OccupancyLog.timestamp >= since,
        )
    ).one()

    avg_power_kw, peak_power_kw, avg_temperature, avg_noise_level = db.execute(
        select(
            func.avg(SensorLog.power_kw),
            func.max(SensorLog.power_kw),
            func.avg(SensorLog.temperature),
            func.avg(SensorLog.noise_level),
        ).where(
            SensorLog.facility_id == facility_id,
            SensorLog.timestamp >= since,
        )
    ).one()

    recommendation_count = len(build_recommendations(db, facility_id))

    return RollupComputation(
        avg_occupancy_rate=round(float(avg_occupancy_rate or 0), 4),
        peak_occupancy_rate=round(float(peak_occupancy_rate or 0), 4),
        high_congestion_events=int(high_congestion_events or 0),
        avg_power_kw=round(float(avg_power_kw), 4) if avg_power_kw is not None else None,
        peak_power_kw=round(float(peak_power_kw), 4) if peak_power_kw is not None else None,
        avg_temperature=round(float(avg_temperature), 4) if avg_temperature is not None else None,
        avg_noise_level=round(float(avg_noise_level), 4) if avg_noise_level is not None else None,
        recommendation_count=recommendation_count,
    )


def compute_and_store_rollup(
    db: Session,
    facility_id: int,
    window_minutes: int = 60,
    *,
    dedupe: bool = True,
) -> FacilityOperationalRollup:
    current_time = utc_now()
    existing = latest_rollup(db, facility_id, window_minutes=window_minutes)
    if dedupe and existing and (current_time - existing.timestamp).total_seconds() < ROLLUP_DEDUP_SECONDS:
        return existing

    metrics = compute_rollup_metrics(db, facility_id, window_minutes=window_minutes)
    rollup = FacilityOperationalRollup(
        facility_id=facility_id,
        timestamp=current_time,
        window_minutes=window_minutes,
        avg_occupancy_rate=metrics.avg_occupancy_rate,
        peak_occupancy_rate=metrics.peak_occupancy_rate,
        high_congestion_events=metrics.high_congestion_events,
        avg_power_kw=metrics.avg_power_kw,
        peak_power_kw=metrics.peak_power_kw,
        avg_temperature=metrics.avg_temperature,
        avg_noise_level=metrics.avg_noise_level,
        recommendation_count=metrics.recommendation_count,
    )
    db.add(rollup)
    db.flush()
    return rollup


def serialize_rollup(rollup: FacilityOperationalRollup) -> FacilityOperationalRollupRead:
    return FacilityOperationalRollupRead.model_validate(rollup)
