from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models import Analysis, Facility
from app.schemas.facility import FacilityCreate, FacilityStatus, FacilityUpdate


def list_facilities(db: Session) -> list[Facility]:
    return list(db.scalars(select(Facility).order_by(Facility.name)).all())


def get_facility_or_none(db: Session, facility_id: int) -> Facility | None:
    return db.get(Facility, facility_id)


def create_facility(db: Session, payload: FacilityCreate) -> Facility:
    facility = Facility(**payload.model_dump())
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


def update_facility(db: Session, facility: Facility, payload: FacilityUpdate) -> Facility:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(facility, key, value)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return facility


def delete_facility(db: Session, facility: Facility) -> None:
    db.delete(facility)
    db.commit()


def latest_analysis_for_facility(db: Session, facility_id: int) -> Analysis | None:
    return db.scalar(
        select(Analysis)
        .where(Analysis.facility_id == facility_id)
        .order_by(desc(Analysis.created_at))
        .limit(1)
    )


def facility_status(db: Session, facility: Facility) -> FacilityStatus:
    latest = latest_analysis_for_facility(db, facility.id)
    if not latest:
        return FacilityStatus(
            facility=facility,
            available_seats=facility.total_seats,
        )
    return FacilityStatus(
        facility=facility,
        people_count=latest.people_count,
        occupied_seats=latest.occupied_seats,
        available_seats=latest.available_seats,
        occupancy_rate=latest.occupancy_rate,
        congestion_level=latest.congestion_level,
        congestion_score=latest.congestion_score,
        latest_analysis_id=latest.id,
        latest_analysis_at=latest.created_at,
    )


def facility_with_recent(db: Session, facility_id: int) -> Facility | None:
    return db.scalar(select(Facility).options(selectinload(Facility.analyses)).where(Facility.id == facility_id))

