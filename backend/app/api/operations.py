from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.operations import JobRunRead, JobStatusRead, OperationalAlertRead
from app.services.alerts import list_active_alerts, refresh_all_operational_alerts, serialize_alert
from app.services.job_runner import current_job_status, list_job_runs

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/job-status", response_model=JobStatusRead)
def job_status(db: Session = Depends(get_db)) -> JobStatusRead:
    refresh_all_operational_alerts(db)
    db.commit()
    return current_job_status(db)


@router.get("/job-runs", response_model=list[JobRunRead])
def job_runs(limit: int = 25, db: Session = Depends(get_db)) -> list[JobRunRead]:
    return [JobRunRead.model_validate(item) for item in list_job_runs(db, limit=min(limit, 100))]


@router.get("/alerts", response_model=list[OperationalAlertRead])
def operations_alerts(db: Session = Depends(get_db)) -> list[OperationalAlertRead]:
    refresh_all_operational_alerts(db)
    db.commit()
    return [serialize_alert(alert) for alert in list_active_alerts(db)]
