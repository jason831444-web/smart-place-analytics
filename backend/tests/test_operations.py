from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models import Facility
from app.services.operations import create_occupancy_log
from app.services.sensors import create_sensor_log


def setup_app_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    return TestingSessionLocal


def test_occupancy_log_creation_and_latest_status_endpoint() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Ops Library", type="Library", location="1F", total_seats=40)
    db.add(facility)
    db.flush()

    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=datetime(2026, 5, 18, 9, 0, 0),
        people_count=18,
        occupied_seats=18,
        available_seats=22,
        occupancy_rate=0.45,
        congestion_score=45,
        congestion_level="Medium",
        confidence=0.81,
        source_type="image_upload",
    )
    facility_id = facility.id
    db.commit()
    db.close()

    try:
        client = TestClient(app)
        response = client.get(f"/api/facilities/{facility_id}/latest-status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["facility_id"] == facility_id
    assert payload["occupancy_rate"] == 0.45
    assert payload["congestion_level"] == "Medium"
    assert payload["source_type"] == "image_upload"


def test_summary_forecast_and_sensor_summary_endpoints() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Ops Lounge", type="Study Room", location="2F", total_seats=30)
    db.add(facility)
    db.flush()

    base_time = datetime(2026, 5, 18, 10, 0, 0)
    for index, rate in enumerate([0.3, 0.55, 0.9, 0.6]):
        occupied = int(rate * facility.total_seats)
        create_occupancy_log(
            db,
            facility_id=facility.id,
            timestamp=base_time + timedelta(minutes=index * 15),
            people_count=occupied,
            occupied_seats=occupied,
            available_seats=facility.total_seats - occupied,
            occupancy_rate=rate,
            congestion_score=round(rate * 100, 2),
            congestion_level="High" if rate > 0.7 else "Medium",
            source_type="webcam",
        )

    create_sensor_log(
        db,
        facility_id=facility.id,
        timestamp=base_time,
        temperature=23.2,
        humidity=46.5,
        power_kw=11.8,
        door_count=16,
        noise_level=57.0,
        source_type="simulator",
    )
    facility_id = facility.id
    db.commit()
    db.close()

    try:
        client = TestClient(app)
        summary_response = client.get(f"/api/facilities/{facility_id}/summary")
        forecast_response = client.get(f"/api/facilities/{facility_id}/forecast?window_minutes=60")
        sensor_summary_response = client.get(f"/api/facilities/{facility_id}/sensor-summary")
    finally:
        app.dependency_overrides.clear()

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["facility_id"] == facility_id
    assert summary["peak_occupancy_rate"] == 0.9
    assert summary["high_congestion_events"] == 1

    assert forecast_response.status_code == 200
    forecast = forecast_response.json()
    assert forecast["facility_id"] == facility_id
    assert forecast["method"] in {"moving_average", "hybrid_moving_average_same_hour", "cold_start_baseline"}
    assert 0 <= forecast["predicted_occupancy_rate"] <= 1

    assert sensor_summary_response.status_code == 200
    sensor_summary = sensor_summary_response.json()
    assert sensor_summary["facility_id"] == facility_id
    assert sensor_summary["latest_power_kw"] == 11.8


def test_empty_operations_endpoints_are_safe_and_invalid_facility_returns_404() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Quiet Room", type="Study Room", location="4F", total_seats=12)
    db.add(facility)
    db.commit()
    facility_id = facility.id
    db.close()

    try:
        client = TestClient(app)
        latest_response = client.get(f"/api/facilities/{facility_id}/latest-status")
        summary_response = client.get(f"/api/facilities/{facility_id}/summary")
        forecast_response = client.get(f"/api/facilities/{facility_id}/forecast")
        missing_response = client.get("/api/facilities/999999/summary")
    finally:
        app.dependency_overrides.clear()

    assert latest_response.status_code == 200
    assert latest_response.json()["occupancy_rate"] == 0
    assert summary_response.status_code == 200
    assert summary_response.json()["samples"] == 0
    assert forecast_response.status_code == 200
    assert forecast_response.json()["method"] == "cold_start_baseline"
    assert missing_response.status_code == 404
