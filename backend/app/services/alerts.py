import json
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import Alert, Facility
from app.schemas.operations import OperationalAlertRead
from app.services.operations import latest_status
from app.services.rollups import latest_rollup
from app.services.sensors import latest_sensor_log
from app.utils.time import utc_now

STALE_TELEMETRY_MINUTES = 10
OVERDUE_ROLLUP_MINUTES = 15
HIGH_CONGESTION_THRESHOLD = 0.85
HIGH_POWER_KW_THRESHOLD = 12.0
LOW_OCCUPANCY_THRESHOLD = 0.35


@dataclass(frozen=True)
class AlertSpec:
    alert_type: str
    severity: str
    title: str
    message: str
    threshold: float
    evidence: list[str]


def _latest_facility_health(facility_id: int, db: Session) -> tuple:
    return latest_status(db, facility_id), latest_sensor_log(db, facility_id), latest_rollup(db, facility_id)


def operational_alert_specs(
    db: Session,
    facility_id: int,
    *,
    stale_telemetry_minutes: int = STALE_TELEMETRY_MINUTES,
    overdue_rollup_minutes: int = OVERDUE_ROLLUP_MINUTES,
) -> list[AlertSpec]:
    status, sensor, rollup = _latest_facility_health(facility_id, db)
    now = utc_now()
    alerts: list[AlertSpec] = []

    telemetry_cutoff = now - timedelta(minutes=stale_telemetry_minutes)
    if sensor is None or sensor.timestamp < telemetry_cutoff:
        evidence = [f"Telemetry cutoff: {stale_telemetry_minutes} minutes."]
        if sensor is not None:
            evidence.append(f"Latest sensor timestamp: {sensor.timestamp.isoformat()}")
        alerts.append(
            AlertSpec(
                alert_type="stale_telemetry",
                severity="high",
                title="Telemetry is stale",
                message="Sensor telemetry is overdue and the facility may be missing recent environmental data.",
                threshold=float(stale_telemetry_minutes),
                evidence=evidence,
            )
        )

    rollup_cutoff = now - timedelta(minutes=overdue_rollup_minutes)
    if rollup is None or rollup.timestamp < rollup_cutoff:
        evidence = [f"Rollup cutoff: {overdue_rollup_minutes} minutes."]
        if rollup is not None:
            evidence.append(f"Latest rollup timestamp: {rollup.timestamp.isoformat()}")
        alerts.append(
            AlertSpec(
                alert_type="overdue_rollup",
                severity="medium",
                title="Operational rollup overdue",
                message="Facility rollups have not been refreshed recently, so dashboard summaries may be stale.",
                threshold=float(overdue_rollup_minutes),
                evidence=evidence,
            )
        )

    if status.occupancy_rate >= HIGH_CONGESTION_THRESHOLD:
        alerts.append(
            AlertSpec(
                alert_type="high_congestion",
                severity="high",
                title="High congestion detected",
                message="Occupancy is in the high congestion range and may require overflow or redirect actions.",
                threshold=HIGH_CONGESTION_THRESHOLD,
                evidence=[
                    f"Occupancy rate: {status.occupancy_rate:.2f}",
                    f"Congestion level: {status.congestion_level}",
                ],
            )
        )

    if (
        sensor is not None
        and sensor.timestamp >= telemetry_cutoff
        and sensor.power_kw >= HIGH_POWER_KW_THRESHOLD
        and status.occupancy_rate <= LOW_OCCUPANCY_THRESHOLD
    ):
        alerts.append(
            AlertSpec(
                alert_type="energy_mismatch",
                severity="medium",
                title="Energy usage exceeds occupancy demand",
                message="Power draw is high relative to current occupancy and may warrant HVAC or lighting adjustment.",
                threshold=HIGH_POWER_KW_THRESHOLD,
                evidence=[
                    f"Power draw: {sensor.power_kw:.1f} kW",
                    f"Occupancy rate: {status.occupancy_rate:.2f}",
                ],
            )
        )

    return alerts


def sync_operational_alerts(
    db: Session,
    facility_id: int,
    *,
    stale_telemetry_minutes: int = STALE_TELEMETRY_MINUTES,
    overdue_rollup_minutes: int = OVERDUE_ROLLUP_MINUTES,
) -> list[Alert]:
    next_specs = operational_alert_specs(
        db,
        facility_id,
        stale_telemetry_minutes=stale_telemetry_minutes,
        overdue_rollup_minutes=overdue_rollup_minutes,
    )
    existing_active = {
        alert.alert_type: alert
        for alert in db.scalars(
            select(Alert).where(Alert.facility_id == facility_id, Alert.status == "active")
        ).all()
    }
    active_types = {spec.alert_type for spec in next_specs}
    now = utc_now()

    for spec in next_specs:
        current = existing_active.get(spec.alert_type)
        if current:
            current.severity = spec.severity
            current.title = spec.title
            current.threshold = spec.threshold
            current.message = spec.message
            current.evidence_json = json.dumps(spec.evidence)
            current.status = "active"
        else:
            db.add(
                Alert(
                    facility_id=facility_id,
                    alert_type=spec.alert_type,
                    severity=spec.severity,
                    title=spec.title,
                    threshold=spec.threshold,
                    triggered_at=now,
                    message=spec.message,
                    evidence_json=json.dumps(spec.evidence),
                    status="active",
                )
            )

    for alert_type, alert in existing_active.items():
        if alert_type not in active_types:
            alert.status = "resolved"

    db.flush()
    return list_active_alerts(db, facility_id=facility_id)


def refresh_all_operational_alerts(
    db: Session,
    *,
    facility_id: int | None = None,
    stale_telemetry_minutes: int = STALE_TELEMETRY_MINUTES,
    overdue_rollup_minutes: int = OVERDUE_ROLLUP_MINUTES,
) -> list[Alert]:
    stmt = select(Facility).order_by(Facility.id)
    if facility_id is not None:
        stmt = stmt.where(Facility.id == facility_id)

    all_alerts: list[Alert] = []
    for facility in db.scalars(stmt).all():
        all_alerts.extend(
            sync_operational_alerts(
                db,
                facility.id,
                stale_telemetry_minutes=stale_telemetry_minutes,
                overdue_rollup_minutes=overdue_rollup_minutes,
            )
        )
    return all_alerts


def list_active_alerts(db: Session, *, facility_id: int | None = None, limit: int = 100) -> list[Alert]:
    stmt = select(Alert).where(Alert.status == "active")
    if facility_id is not None:
        stmt = stmt.where(Alert.facility_id == facility_id)
    stmt = stmt.order_by(desc(Alert.triggered_at)).limit(limit)
    return list(db.scalars(stmt).all())


def active_alert_count(db: Session, *, facility_id: int | None = None) -> int:
    stmt = select(func.count(Alert.id)).where(Alert.status == "active")
    if facility_id is not None:
        stmt = stmt.where(Alert.facility_id == facility_id)
    return int(db.scalar(stmt) or 0)


def serialize_alert(alert: Alert) -> OperationalAlertRead:
    evidence: list[str] = []
    if alert.evidence_json:
        try:
            decoded = json.loads(alert.evidence_json)
            if isinstance(decoded, list):
                evidence = [str(entry) for entry in decoded]
        except json.JSONDecodeError:
            evidence = [alert.evidence_json]

    return OperationalAlertRead(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        facility_id=alert.facility_id,
        evidence=evidence,
        status=alert.status,
        created_at=alert.triggered_at,
    )
