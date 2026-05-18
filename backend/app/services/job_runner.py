import time
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal
from app.models import Facility, FacilityOperationalRollup, JobRun, SensorLog
from app.schemas.operations import JobRunRead, JobStatusRead
from app.services.alerts import active_alert_count, sync_operational_alerts
from app.services.operations import latest_status
from app.services.rollups import compute_and_store_rollup
from app.services.sensors import create_sensor_log, simulated_sensor_payload
from app.utils.time import utc_now


@dataclass(frozen=True)
class JobIterationResult:
    status: str
    facilities_processed: int
    generated_sensor_logs: int
    computed_rollups: int
    error_message: str | None = None
    job_run_id: int | None = None


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
    session_factory: sessionmaker = SessionLocal,
) -> JobIterationResult:
    started_at = utc_now()
    facilities_processed = 0
    generated_sensor_logs = 0
    computed_rollups_count = 0
    errors: list[str] = []
    status = "success"
    job_run_error_message: str | None = None
    job_run_id: int | None = None

    session = session_factory()
    try:
        try:
            for facility in active_facilities(session, facility_id=facility_id):
                try:
                    if generate_sensors:
                        facility_status = latest_status(session, facility.id)
                        payload = simulated_sensor_payload(facility, facility_status.occupancy_rate)
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

                    sync_operational_alerts(session, facility.id)
                    session.commit()
                    facilities_processed += 1
                except Exception as exc:  # pragma: no cover - covered via result assertions rather than exact exceptions
                    session.rollback()
                    errors.append(f"Facility {facility.id}: {exc}")
        except Exception as exc:  # pragma: no cover - defensive guard for top-level iteration failures
            session.rollback()
            errors.append(f"Job iteration failed: {exc}")

        finished_at = utc_now()
        status = "failed" if facilities_processed == 0 and errors else "partial" if errors else "success"
        job_run = JobRun(
            job_name="operations_pipeline",
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=max(int((finished_at - started_at).total_seconds() * 1000), 0),
            facilities_processed=facilities_processed,
            sensors_generated=generated_sensor_logs,
            rollups_computed=computed_rollups_count,
            error_message=" | ".join(errors)[:4000] if errors else None,
        )
        session.add(job_run)
        session.commit()
        session.refresh(job_run)
        job_run_error_message = job_run.error_message
        job_run_id = job_run.id
    finally:
        session.close()

    return JobIterationResult(
        status=status,
        facilities_processed=facilities_processed,
        generated_sensor_logs=generated_sensor_logs,
        computed_rollups=computed_rollups_count,
        error_message=job_run_error_message,
        job_run_id=job_run_id,
    )


def run_loop(
    *,
    interval_seconds: int = 30,
    facility_id: int | None = None,
    iterations: int = 0,
    generate_sensors: bool = True,
    compute_rollups: bool = True,
    window_minutes: int = 60,
    session_factory: sessionmaker = SessionLocal,
) -> None:
    completed = 0
    try:
        while iterations == 0 or completed < iterations:
            run_iteration(
                facility_id=facility_id,
                generate_sensors=generate_sensors,
                compute_rollups=compute_rollups,
                window_minutes=window_minutes,
                session_factory=session_factory,
            )
            completed += 1
            if iterations == 0 or completed < iterations:
                time.sleep(max(interval_seconds, 1))
    except KeyboardInterrupt:
        return


def list_job_runs(db: Session, limit: int = 50) -> list[JobRun]:
    return list(db.scalars(select(JobRun).order_by(JobRun.started_at.desc()).limit(limit)).all())


def current_job_status(db: Session) -> JobStatusRead:
    recent_cutoff = utc_now() - timedelta(minutes=60)
    latest_job_run = db.scalar(select(JobRun).order_by(JobRun.started_at.desc()).limit(1))
    latest_sensor_log_at = db.scalar(select(func.max(SensorLog.timestamp)))
    latest_rollup_at = db.scalar(select(func.max(FacilityOperationalRollup.timestamp)))
    total_sensor_logs = int(db.scalar(select(func.count(SensorLog.id))) or 0)
    total_rollups = int(db.scalar(select(func.count(FacilityOperationalRollup.id))) or 0)
    current_active_alert_count = active_alert_count(db)
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
        latest_job_run=JobRunRead.model_validate(latest_job_run) if latest_job_run else None,
        latest_sensor_log_at=latest_sensor_log_at,
        latest_rollup_at=latest_rollup_at,
        total_sensor_logs=total_sensor_logs,
        total_rollups=total_rollups,
        active_alert_count=current_active_alert_count,
        facilities_with_recent_activity=facilities_with_recent_activity,
        generated_at=utc_now(),
    )
