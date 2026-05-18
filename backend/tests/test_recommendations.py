from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models import Facility
from app.services.operations import create_occupancy_log
from app.services.recommendations import build_recommendations
from app.services.sensors import create_sensor_log


def make_db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_recommendation_engine_flags_high_occupancy_and_energy_mismatch() -> None:
    db = make_db()
    facility = Facility(name="Recommendation Hall", type="Library", location="3F", total_seats=40)
    db.add(facility)
    db.flush()

    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=datetime(2026, 5, 18, 14, 0, 0),
        people_count=36,
        occupied_seats=36,
        available_seats=4,
        occupancy_rate=0.9,
        congestion_score=90,
        congestion_level="High",
        source_type="webcam",
    )
    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=datetime(2026, 5, 18, 13, 0, 0),
        people_count=34,
        occupied_seats=34,
        available_seats=6,
        occupancy_rate=0.85,
        congestion_score=85,
        congestion_level="High",
        source_type="webcam",
    )
    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=datetime(2026, 5, 17, 14, 0, 0),
        people_count=35,
        occupied_seats=35,
        available_seats=5,
        occupancy_rate=0.875,
        congestion_score=87.5,
        congestion_level="High",
        source_type="image_upload",
    )
    create_sensor_log(
        db,
        facility_id=facility.id,
        timestamp=datetime(2026, 5, 18, 14, 0, 0),
        temperature=24.0,
        humidity=49.0,
        power_kw=15.4,
        door_count=18,
        noise_level=61.0,
        source_type="simulator",
    )
    db.commit()

    recommendations = build_recommendations(db, facility.id)
    recommendation_types = {item.recommendation_type for item in recommendations}

    assert "occupancy_redirect" in recommendation_types
    assert "staffing_schedule_adjustment" in recommendation_types
