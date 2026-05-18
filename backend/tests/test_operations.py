from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models import Facility, JobRun
from app.services.alerts import refresh_all_operational_alerts
from app.services.job_runner import run_iteration
from app.services.operations import create_occupancy_log
from app.services.rollups import compute_and_store_rollup
from app.services.sensors import create_sensor_log
from app.utils.time import utc_now


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


def test_rollup_computation_with_sensor_data_and_latest_rollup_endpoint() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Signal Commons", type="Library", location="5F", total_seats=50)
    db.add(facility)
    db.flush()

    base_time = utc_now() - timedelta(minutes=20)
    for index, rate in enumerate([0.4, 0.72, 0.88]):
        occupied = int(rate * facility.total_seats)
        create_occupancy_log(
            db,
            facility_id=facility.id,
            timestamp=base_time + timedelta(minutes=index * 10),
            people_count=occupied,
            occupied_seats=occupied,
            available_seats=facility.total_seats - occupied,
            occupancy_rate=rate,
            congestion_score=round(rate * 100, 2),
            congestion_level="High" if rate >= 0.71 else "Medium",
            source_type="webcam",
        )

    for index, power_kw in enumerate([10.2, 12.4, 11.6]):
        create_sensor_log(
            db,
            facility_id=facility.id,
            timestamp=base_time + timedelta(minutes=index * 10),
            temperature=22.5 + index,
            humidity=44.0 + index,
            power_kw=power_kw,
            door_count=14 + index,
            noise_level=54.0 + index,
            source_type="simulator",
        )

    rollup = compute_and_store_rollup(db, facility.id, window_minutes=180, dedupe=False)
    facility_id = facility.id
    db.commit()
    db.refresh(rollup)
    db.close()

    try:
        client = TestClient(app)
        latest_rollup_response = client.get(f"/api/facilities/{facility_id}/rollups/latest")
        rollups_response = client.get(f"/api/facilities/{facility_id}/rollups")
    finally:
        app.dependency_overrides.clear()

    assert latest_rollup_response.status_code == 200
    latest_rollup = latest_rollup_response.json()
    assert latest_rollup["facility_id"] == facility_id
    assert latest_rollup["window_minutes"] == 180
    assert latest_rollup["peak_occupancy_rate"] == 0.88
    assert latest_rollup["high_congestion_events"] == 2
    assert latest_rollup["avg_power_kw"] == 11.4

    assert rollups_response.status_code == 200
    rollups = rollups_response.json()
    assert len(rollups) == 1
    assert rollups[0]["recommendation_count"] >= 0


def test_rollup_computation_is_safe_when_sensor_data_is_missing() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Quiet Nook", type="Study Room", location="1F", total_seats=16)
    db.add(facility)
    db.flush()

    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=utc_now() - timedelta(minutes=15),
        people_count=5,
        occupied_seats=5,
        available_seats=11,
        occupancy_rate=0.3125,
        congestion_score=31.25,
        congestion_level="Medium",
        source_type="image_upload",
    )

    rollup = compute_and_store_rollup(db, facility.id, window_minutes=60, dedupe=False)
    db.commit()
    db.refresh(rollup)

    assert rollup.avg_occupancy_rate == 0.3125
    assert rollup.peak_occupancy_rate == 0.3125
    assert rollup.avg_power_kw is None
    assert rollup.peak_power_kw is None
    assert rollup.avg_temperature is None
    assert rollup.avg_noise_level is None

    db.close()


def test_job_status_endpoint_reports_recent_background_activity() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Atrium", type="Cafe", location="Ground", total_seats=28)
    db.add(facility)
    db.flush()

    create_sensor_log(
        db,
        facility_id=facility.id,
        timestamp=utc_now(),
        temperature=23.1,
        humidity=48.0,
        power_kw=9.4,
        door_count=18,
        noise_level=61.0,
        source_type="simulator",
    )
    compute_and_store_rollup(db, facility.id, window_minutes=60, dedupe=False)
    db.commit()
    db.close()

    try:
        client = TestClient(app)
        response = client.get("/api/operations/job-status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_sensor_logs"] == 1
    assert payload["total_rollups"] == 1
    assert payload["facilities_with_recent_activity"] == 1
    assert payload["latest_sensor_log_at"] is not None
    assert payload["latest_rollup_at"] is not None
    assert payload["generated_at"] is not None


def test_job_run_is_created_after_job_iteration() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="North Hall", type="Library", location="3F", total_seats=20)
    db.add(facility)
    db.commit()
    db.close()

    result = run_iteration(
        generate_sensors=True,
        compute_rollups=True,
        window_minutes=60,
        session_factory=TestingSessionLocal,
    )

    db = TestingSessionLocal()
    job_runs = db.query(JobRun).all()
    db.close()
    app.dependency_overrides.clear()

    assert result.status == "success"
    assert result.facilities_processed == 1
    assert len(job_runs) == 1
    assert job_runs[0].job_name == "operations_pipeline"
    assert job_runs[0].status == "success"
    assert job_runs[0].sensors_generated == 1
    assert job_runs[0].rollups_computed == 1


def test_stale_telemetry_and_overdue_rollup_alert_generation() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Annex", type="Study Room", location="Basement", total_seats=10)
    db.add(facility)
    db.flush()

    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=utc_now() - timedelta(minutes=5),
        people_count=2,
        occupied_seats=2,
        available_seats=8,
        occupancy_rate=0.2,
        congestion_score=20,
        congestion_level="Low",
        source_type="image_upload",
    )
    db.commit()

    alerts = refresh_all_operational_alerts(db, facility_id=facility.id)
    alert_types = {alert.alert_type for alert in alerts}
    db.commit()
    db.close()
    app.dependency_overrides.clear()

    assert "stale_telemetry" in alert_types
    assert "overdue_rollup" in alert_types


def test_operations_alerts_endpoint_returns_expected_shape() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="Commons", type="Cafe", location="Lobby", total_seats=24)
    db.add(facility)
    db.flush()

    create_occupancy_log(
        db,
        facility_id=facility.id,
        timestamp=utc_now() - timedelta(minutes=2),
        people_count=22,
        occupied_seats=22,
        available_seats=2,
        occupancy_rate=0.92,
        congestion_score=92,
        congestion_level="High",
        source_type="webcam",
    )
    db.commit()
    db.close()

    try:
        client = TestClient(app)
        response = client.get("/api/operations/alerts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload
    assert {"alert_type", "severity", "title", "message", "facility_id", "evidence", "created_at"}.issubset(payload[0].keys())


def test_job_status_includes_latest_job_run() -> None:
    TestingSessionLocal = setup_app_db()
    db = TestingSessionLocal()
    facility = Facility(name="West Wing", type="Library", location="2F", total_seats=18)
    db.add(facility)
    db.commit()
    db.close()

    run_iteration(
        generate_sensors=True,
        compute_rollups=False,
        session_factory=TestingSessionLocal,
    )

    try:
        client = TestClient(app)
        response = client.get("/api/operations/job-status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest_job_run"] is not None
    assert payload["latest_job_run"]["job_name"] == "operations_pipeline"
    assert payload["latest_job_run"]["status"] == "success"
