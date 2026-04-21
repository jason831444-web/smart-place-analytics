from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.analytics import AnalyticsOverview, FacilityAnalytics
from app.schemas.facility import FacilityCreate, FacilityRead, FacilityUpdate
from app.services import analytics as analytics_service
from app.services.facilities import create_facility, delete_facility, get_facility_or_none, list_facilities, update_facility

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/facilities", response_model=list[FacilityRead])
def admin_facilities(db: Session = Depends(get_db)) -> list[FacilityRead]:
    return list_facilities(db)


@router.post("/facilities", response_model=FacilityRead, status_code=201)
def admin_create_facility(payload: FacilityCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> FacilityRead:
    return create_facility(db, payload)


@router.put("/facilities/{facility_id}", response_model=FacilityRead)
def admin_update_facility(facility_id: int, payload: FacilityUpdate, db: Session = Depends(get_db)) -> FacilityRead:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return update_facility(db, facility, payload)


@router.delete("/facilities/{facility_id}", status_code=204)
def admin_delete_facility(facility_id: int, db: Session = Depends(get_db)) -> None:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    delete_facility(db, facility)


@router.get("/analytics/overview", response_model=AnalyticsOverview)
def analytics_overview(db: Session = Depends(get_db)) -> AnalyticsOverview:
    return AnalyticsOverview(
        **analytics_service.overview_stats(db),
        busiest_facilities=analytics_service.busiest_facilities(db),
        peak_hours=analytics_service.peak_hours(db),
        recent_activity=analytics_service.recent_activity(db),
    )


@router.get("/analytics/facilities/{facility_id}", response_model=FacilityAnalytics)
def facility_analytics(facility_id: int, db: Session = Depends(get_db)) -> FacilityAnalytics:
    facility = get_facility_or_none(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    stats = analytics_service.overview_stats(db)
    logs = [item for item in analytics_service.busiest_facilities(db, limit=100) if item.facility_id == facility_id]
    metric = logs[0] if logs else None
    return FacilityAnalytics(
        facility_id=facility_id,
        average_occupancy_rate=metric.average_occupancy_rate if metric else stats["average_occupancy_rate"],
        average_congestion_score=metric.average_congestion_score if metric else stats["average_congestion_score"],
        peak_hours=analytics_service.peak_hours(db, facility_id=facility_id),
        daily_trend=analytics_service.daily_trend(db, facility_id=facility_id),
        recent_activity=analytics_service.recent_activity(db, facility_id=facility_id),
    )

