import time
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Facility, FacilityOperationalRollup, SensorLog
from app.schemas.operations import JobStatusRead
from app.services.operations import latest_status
from app.services.rollups import compute_and_store_rollup
from app.services.sensors import create_sensor_log, simulated_sensor_payload
from app.utils.time import utc_now


@dataclass(frozen=True)
class JobIterationResult:
    generated_sensor_logs: int
    computed_rollups: int


def active_facilities(session, facility_id: int | None = None) -> list[Facility]:
    stmt = select(Facility).order_by(Facility.id)
    if facility_id is not None:
        stmt = stmt.where(Facility.id == facility_id)
    return list(session.scalars(stmt).all())


def run_iteration(
    *,
    facility_id: int | None = None,
    generate_sensors: bool = True,
    compute_rollups: bool = True,
    window_minutes: int = 60,
) -> JobIterationResult:
    generated_sensor_logs = 0
    computed_rollups_count = 0

    session = SessionLocal()
    try:
        for facility in active_facilities(session, facility_id=facility_id):
            if generate_sensors:
                status = latest_status(session, facility.id)
                payload = simulated_sensor_payload(facility, status.occupancy_rate)
                create_sensor_log(
                    session,
                    facility_id=facility.id,
                    timestamp=utc_now(),
                    source_type="simulator",
                    **payload,
                )
                generated_sensor_logs += 1

            if compute_rollups:
                compute_and_store_rollup(session, facility.id, window_minutes=window_minutes)
                computed_rollups_count += 1

        session.commit()
    finally:
        session.close()

    return JobIterationResult(
        generated_sensor_logs=generated_sensor_logs,
        computed_rollups=computed_rollups_count,
    )


def run_loop(
    *,
    interval_seconds: int = 30,
    facility_id: int | None = None,
    iterations: int = 0,
    generate_sensors: bool = True,
    compute_rollups: bool = True,
    window_minutes: int = 60,
) -> None:
    completed = 0
    try:
        while iterations == 0 or completed < iterations:
            run_iteration(
                facility_id=facility_id,
                generate_sensors=generate_sensors,
                compute_rollups=compute_rollups,
                window_minutes=window_minutes,
            )
            completed += 1
            if iterations == 0 or completed < iterations:
                time.sleep(max(interval_seconds, 1))
    except KeyboardInterrupt:
        return


def current_job_status(db: Session) -> JobStatusRead:
    recent_cutoff = utc_now() - timedelta(minutes=60)
    latest_sensor_log_at = db.scalar(select(func.max(SensorLog.timestamp)))
    latest_rollup_at = db.scalar(select(func.max(FacilityOperationalRollup.timestamp)))
    total_sensor_logs = int(db.scalar(select(func.count(SensorLog.id))) or 0)
    total_rollups = int(db.scalar(select(func.count(FacilityOperationalRollup.id))) or 0)
    facilities_with_recent_activity = int(
        db.scalar(select(func.count(distinct(SensorLog.facility_id))).where(SensorLog.timestamp >= recent_cutoff)) or 0
    )
    if latest_rollup_at:
        rollup_recent = int(
            db.scalar(
                select(func.count(distinct(FacilityOperationalRollup.facility_id))).where(
                    FacilityOperationalRollup.timestamp >= recent_cutoff
                )
            )
            or 0
        )
        facilities_with_recent_activity = max(facilities_with_recent_activity, rollup_recent)

    return JobStatusRead(
        latest_sensor_log_at=latest_sensor_log_at,
        latest_rollup_at=latest_rollup_at,
        total_sensor_logs=total_sensor_logs,
        total_rollups=total_rollups,
        facilities_with_recent_activity=facilities_with_recent_activity,
        generated_at=utc_now(),
    )
