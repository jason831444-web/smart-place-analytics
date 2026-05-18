from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.models import OccupancyLog
from app.schemas.operations import ForecastRead
from app.services.congestion import congestion_level_for_rate
from app.utils.time import utc_now


@dataclass(frozen=True)
class ForecastResult:
    predicted_occupancy_rate: float
    predicted_congestion_level: str
    confidence: float
    method: str
    explanation: str


def _moving_average(db: Session, facility_id: int, sample_limit: int = 12) -> list[float]:
    rows = db.scalars(
        select(OccupancyLog.occupancy_rate)
        .where(OccupancyLog.facility_id == facility_id)
        .order_by(OccupancyLog.timestamp.desc())
        .limit(sample_limit)
    ).all()
    return [float(value) for value in rows]


def _same_hour_average(db: Session, facility_id: int, timestamp: datetime, days: int = 21) -> list[float]:
    since = timestamp - timedelta(days=days)
    rows = db.scalars(
        select(OccupancyLog.occupancy_rate)
        .where(
            OccupancyLog.facility_id == facility_id,
            OccupancyLog.timestamp >= since,
            extract("hour", OccupancyLog.timestamp) == timestamp.hour,
        )
    ).all()
    return [float(value) for value in rows]


def forecast_occupancy(db: Session, facility_id: int, window_minutes: int = 60, now: datetime | None = None) -> ForecastResult:
    now = now or utc_now()
    moving_average_samples = _moving_average(db, facility_id)
    hourly_samples = _same_hour_average(db, facility_id, now)

    if moving_average_samples and hourly_samples:
        moving_average = sum(moving_average_samples) / len(moving_average_samples)
        same_hour_average = sum(hourly_samples) / len(hourly_samples)
        predicted_rate = (moving_average * 0.6) + (same_hour_average * 0.4)
        confidence = min(0.95, 0.45 + (len(moving_average_samples) * 0.03) + (len(hourly_samples) * 0.02))
        method = "hybrid_moving_average_same_hour"
        explanation = (
            f"Blended the last {len(moving_average_samples)} occupancy samples with "
            f"{len(hourly_samples)} same-hour historical samples for the next {window_minutes} minutes."
        )
    elif moving_average_samples:
        predicted_rate = sum(moving_average_samples) / len(moving_average_samples)
        confidence = min(0.75, 0.35 + (len(moving_average_samples) * 0.04))
        method = "moving_average"
        explanation = f"Used the last {len(moving_average_samples)} occupancy samples for the next {window_minutes} minutes."
    else:
        predicted_rate = 0.0
        confidence = 0.2
        method = "cold_start_baseline"
        explanation = "No historical occupancy samples were available, so the forecast fell back to a cold-start baseline."

    predicted_rate = max(0.0, min(round(predicted_rate, 4), 1.0))
    return ForecastResult(
        predicted_occupancy_rate=predicted_rate,
        predicted_congestion_level=congestion_level_for_rate(predicted_rate),
        confidence=round(confidence, 2),
        method=method,
        explanation=explanation,
    )


def forecast_response(db: Session, facility_id: int, window_minutes: int = 60) -> ForecastRead:
    result = forecast_occupancy(db, facility_id, window_minutes=window_minutes)
    return ForecastRead(
        facility_id=facility_id,
        window_minutes=window_minutes,
        predicted_occupancy_rate=result.predicted_occupancy_rate,
        predicted_congestion_level=result.predicted_congestion_level,
        confidence=result.confidence,
        method=result.method,
        explanation=result.explanation,
        generated_at=utc_now(),
    )
