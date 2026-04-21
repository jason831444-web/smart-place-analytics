from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import Base
from app.models import Analysis, Facility, OccupancyLog, Upload
from app.services.analytics import busiest_facilities, overview_stats, peak_hours


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_analytics_overview_and_rankings() -> None:
    db = make_session()
    facility_a = Facility(name="A", type="Library", location="1F", total_seats=10)
    facility_b = Facility(name="B", type="Cafe", location="2F", total_seats=20)
    db.add_all([facility_a, facility_b])
    db.flush()

    upload_a = Upload(facility_id=facility_a.id, file_path="a.jpg", original_filename="a.jpg")
    upload_b = Upload(facility_id=facility_b.id, file_path="b.jpg", original_filename="b.jpg")
    db.add_all([upload_a, upload_b])
    db.flush()

    analysis_a = Analysis(
        facility_id=facility_a.id,
        upload_id=upload_a.id,
        people_count=8,
        occupied_seats=8,
        available_seats=2,
        occupancy_rate=0.8,
        congestion_level="High",
        congestion_score=80,
        created_at=datetime(2026, 4, 21, 13),
    )
    analysis_b = Analysis(
        facility_id=facility_b.id,
        upload_id=upload_b.id,
        people_count=6,
        occupied_seats=6,
        available_seats=14,
        occupancy_rate=0.3,
        congestion_level="Low",
        congestion_score=30,
        created_at=datetime(2026, 4, 21, 9),
    )
    db.add_all([analysis_a, analysis_b])
    db.flush()
    db.add_all(
        [
            OccupancyLog(
                facility_id=facility_a.id,
                analysis_id=analysis_a.id,
                timestamp=datetime(2026, 4, 21, 13),
                people_count=8,
                occupied_seats=8,
                available_seats=2,
                occupancy_rate=0.8,
                congestion_score=80,
                congestion_level="High",
            ),
            OccupancyLog(
                facility_id=facility_b.id,
                analysis_id=analysis_b.id,
                timestamp=datetime(2026, 4, 21, 9),
                people_count=6,
                occupied_seats=6,
                available_seats=14,
                occupancy_rate=0.3,
                congestion_score=30,
                congestion_level="Low",
            ),
        ]
    )
    db.commit()

    stats = overview_stats(db)
    ranked = busiest_facilities(db)
    hours = peak_hours(db, days=3650)

    assert stats["facilities_count"] == 2
    assert stats["analyses_count"] == 2
    assert stats["average_occupancy_rate"] == 0.55
    assert ranked[0].facility_name == "A"
    assert {hour.hour for hour in hours} == {9, 13}

