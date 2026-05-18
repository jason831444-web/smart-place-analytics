import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import Facility, OccupancyLog, SensorLog
from scripts.run_demo_scenario import apply_scenario


def scenario_sessionmaker():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def seed_facility(SessionLocal) -> int:
    db = SessionLocal()
    try:
        facility = Facility(
            name="Scenario Test Library",
            type="Library",
            location="1F",
            total_seats=40,
            seat_usage_factor=1.0,
        )
        db.add(facility)
        db.commit()
        db.refresh(facility)
        return facility.id
    finally:
        db.close()


def test_scenario_generator_creates_occupancy_logs(monkeypatch) -> None:
    SessionLocal = scenario_sessionmaker()
    facility_id = seed_facility(SessionLocal)
    monkeypatch.setattr("scripts.run_demo_scenario.SessionLocal", SessionLocal)

    result = apply_scenario(scenario="normal_day", facility_id=facility_id, clear_existing=True)

    db = SessionLocal()
    try:
        count = len(list(db.scalars(select(OccupancyLog).where(OccupancyLog.facility_id == facility_id)).all()))
    finally:
        db.close()

    assert result["occupancy_logs_created"] > 0
    assert count == result["occupancy_logs_created"]


def test_scenario_generator_creates_sensor_logs(monkeypatch) -> None:
    SessionLocal = scenario_sessionmaker()
    facility_id = seed_facility(SessionLocal)
    monkeypatch.setattr("scripts.run_demo_scenario.SessionLocal", SessionLocal)

    result = apply_scenario(scenario="normal_day", facility_id=facility_id, clear_existing=True)

    db = SessionLocal()
    try:
        count = len(list(db.scalars(select(SensorLog).where(SensorLog.facility_id == facility_id)).all()))
    finally:
        db.close()

    assert result["sensor_logs_created"] > 0
    assert count == result["sensor_logs_created"]


def test_exam_week_congestion_produces_high_occupancy(monkeypatch) -> None:
    SessionLocal = scenario_sessionmaker()
    facility_id = seed_facility(SessionLocal)
    monkeypatch.setattr("scripts.run_demo_scenario.SessionLocal", SessionLocal)

    apply_scenario(scenario="exam_week_congestion", facility_id=facility_id, clear_existing=True)

    db = SessionLocal()
    try:
        peak_rate = max(log.occupancy_rate for log in db.scalars(select(OccupancyLog).where(OccupancyLog.facility_id == facility_id)).all())
    finally:
        db.close()

    assert peak_rate >= 0.85


def test_low_occupancy_energy_waste_produces_low_occupancy_high_power(monkeypatch) -> None:
    SessionLocal = scenario_sessionmaker()
    facility_id = seed_facility(SessionLocal)
    monkeypatch.setattr("scripts.run_demo_scenario.SessionLocal", SessionLocal)

    apply_scenario(scenario="low_occupancy_energy_waste", facility_id=facility_id, clear_existing=True)

    db = SessionLocal()
    try:
        occupancy_rates = [log.occupancy_rate for log in db.scalars(select(OccupancyLog).where(OccupancyLog.facility_id == facility_id)).all()]
        power_levels = [log.power_kw for log in db.scalars(select(SensorLog).where(SensorLog.facility_id == facility_id)).all()]
    finally:
        db.close()

    assert max(occupancy_rates) < 0.35
    assert min(power_levels) >= 13.8


def test_invalid_scenario_name_fails_clearly(monkeypatch) -> None:
    SessionLocal = scenario_sessionmaker()
    facility_id = seed_facility(SessionLocal)
    monkeypatch.setattr("scripts.run_demo_scenario.SessionLocal", SessionLocal)

    with pytest.raises(ValueError, match="Unknown scenario"):
        apply_scenario(scenario="not_a_real_scenario", facility_id=facility_id)
