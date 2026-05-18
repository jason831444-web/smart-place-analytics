from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.operations import JobStatusRead
from app.services.job_runner import current_job_status

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/job-status", response_model=JobStatusRead)
def job_status(db: Session = Depends(get_db)) -> JobStatusRead:
    return current_job_status(db)
