from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import HistoryPoint
from app.schemas.facility import FacilityRead, FacilityStatus
from app.services.analysis import list_history
from app.services.facilities import facility_status, get_facility_or_none, list_facilities

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityStatus])
def facilities(db: Session = Depends(get_db)) -> list[FacilityStatus]:
    return [facility_status(db, facility) for facility in list_facilities(db)]


@router.get("/{facility_id}", response_model=FacilityRead)
def facility_detail(facility_id: int, db: Session = Depends(get_db)) -> FacilityRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


@router.get("/{facility_id}/status", response_model=FacilityStatus)
def status(facility_id: int, db: Session = Depends(get_db)) -> FacilityStatus:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility_status(db, facility)


@router.get("/{facility_id}/history", response_model=list[HistoryPoint])
def history(facility_id: int, limit: int = 100, db: Session = Depends(get_db)) -> list[HistoryPoint]:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return list_history(db, facility_id, limit=min(limit, 500))

