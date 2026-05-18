from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import SensorLog
from app.schemas.operations import SensorLogRead, SensorSummaryRead


def create_sensor_log(
    db: Session,
    *,
    facility_id: int,
    timestamp: datetime,
    temperature: float,
    humidity: float,
    power_kw: float,
    door_count: int,
    noise_level: float,
    source_type: str = "simulator",
) -> SensorLog:
    log = SensorLog(
        facility_id=facility_id,
        timestamp=timestamp,
        temperature=temperature,
        humidity=humidity,
        power_kw=power_kw,
        door_count=door_count,
        noise_level=noise_level,
        source_type=source_type,
    )
    db.add(log)
    db.flush()
    return log


def list_sensor_logs(db: Session, facility_id: int, limit: int = 200) -> list[SensorLogRead]:
    rows = db.scalars(
        select(SensorLog)
        .where(SensorLog.facility_id == facility_id)
        .order_by(desc(SensorLog.timestamp))
        .limit(limit)
    ).all()
    return [SensorLogRead.model_validate(row) for row in rows]


def latest_sensor_log(db: Session, facility_id: int) -> SensorLog | None:
    return db.scalar(
        select(SensorLog)
        .where(SensorLog.facility_id == facility_id)
        .order_by(desc(SensorLog.timestamp))
        .limit(1)
    )


def sensor_summary(db: Session, facility_id: int) -> SensorSummaryRead:
    latest = latest_sensor_log(db, facility_id)
    avg_temperature, avg_humidity, avg_power, total_door_count, avg_noise, recent_timestamp, samples = db.execute(
        select(
            func.avg(SensorLog.temperature),
            func.avg(SensorLog.humidity),
            func.avg(SensorLog.power_kw),
            func.coalesce(func.sum(SensorLog.door_count), 0),
            func.avg(SensorLog.noise_level),
            func.max(SensorLog.timestamp),
            func.count(SensorLog.id),
        ).where(SensorLog.facility_id == facility_id)
    ).one()

    return SensorSummaryRead(
        facility_id=facility_id,
        latest_temperature=latest.temperature if latest else None,
        latest_humidity=latest.humidity if latest else None,
        latest_power_kw=latest.power_kw if latest else None,
        latest_door_count=latest.door_count if latest else None,
        latest_noise_level=latest.noise_level if latest else None,
        average_temperature=round(float(avg_temperature or 0), 2),
        average_humidity=round(float(avg_humidity or 0), 2),
        average_power_kw=round(float(avg_power or 0), 2),
        total_door_count=int(total_door_count or 0),
        average_noise_level=round(float(avg_noise or 0), 2),
        most_recent_timestamp=recent_timestamp,
        samples=int(samples or 0),
    )
