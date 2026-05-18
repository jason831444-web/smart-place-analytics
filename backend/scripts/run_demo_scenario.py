import argparse
import math
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models import Alert, Facility, FacilityOperationalRollup, OccupancyLog, SensorLog
from app.services.alerts import sync_operational_alerts
from app.services.congestion import calculate_congestion
from app.services.operations import create_occupancy_log
from app.services.rollups import compute_and_store_rollup
from app.services.sensors import create_sensor_log
from app.utils.time import utc_now


SCENARIOS = {
    "exam_week_congestion",
    "low_occupancy_energy_waste",
    "telemetry_outage",
    "normal_day",
}


@dataclass(frozen=True)
class ScenarioPoint:
    timestamp: object
    people_count: int
    temperature: float
    humidity: float
    power_kw: float
    door_count: int
    noise_level: float
    create_sensor: bool = True


def _scenario_progress(index: int, total_points: int) -> float:
    if total_points <= 1:
        return 1.0
    return index / float(total_points - 1)


def _normal_day_points(facility: Facility, hours: int, interval_minutes: int) -> list[ScenarioPoint]:
    total_points = max(int((hours * 60) / interval_minutes), 1)
    start_time = utc_now() - timedelta(hours=hours)
    points: list[ScenarioPoint] = []
    for index in range(total_points):
        progress = _scenario_progress(index, total_points)
        occupancy_rate = 0.38 + math.sin(progress * math.pi) * 0.22
        people_count = max(1, round(occupancy_rate * facility.total_seats))
        timestamp = start_time + timedelta(minutes=index * interval_minutes)
        points.append(
            ScenarioPoint(
                timestamp=timestamp,
                people_count=people_count,
                temperature=round(21.6 + occupancy_rate * 2.0, 2),
                humidity=round(40.5 + occupancy_rate * 6.0, 2),
                power_kw=round(7.0 + occupancy_rate * 5.5, 2),
                door_count=max(2, round(6 + occupancy_rate * 28)),
                noise_level=round(43.0 + occupancy_rate * 14.0, 2),
            )
        )
    return points


def _exam_week_congestion_points(facility: Facility, hours: int, interval_minutes: int) -> list[ScenarioPoint]:
    total_points = max(int((hours * 60) / interval_minutes), 1)
    start_time = utc_now() - timedelta(hours=hours)
    points: list[ScenarioPoint] = []
    for index in range(total_points):
        progress = _scenario_progress(index, total_points)
        occupancy_rate = min(0.35 + progress * 0.62, 0.97)
        people_count = max(1, round(occupancy_rate * facility.total_seats))
        timestamp = start_time + timedelta(minutes=index * interval_minutes)
        points.append(
            ScenarioPoint(
                timestamp=timestamp,
                people_count=people_count,
                temperature=round(22.0 + occupancy_rate * 2.8, 2),
                humidity=round(42.0 + occupancy_rate * 8.5, 2),
                power_kw=round(8.5 + occupancy_rate * 7.8, 2),
                door_count=max(4, round(10 + occupancy_rate * 40)),
                noise_level=round(47.0 + occupancy_rate * 22.0, 2),
            )
        )
    return points


def _low_occupancy_energy_waste_points(facility: Facility, hours: int, interval_minutes: int) -> list[ScenarioPoint]:
    total_points = max(int((hours * 60) / interval_minutes), 1)
    start_time = utc_now() - timedelta(hours=hours)
    points: list[ScenarioPoint] = []
    for index in range(total_points):
        progress = _scenario_progress(index, total_points)
        occupancy_rate = 0.10 + (0.06 * math.sin(progress * math.pi * 2))
        people_count = max(0, round(occupancy_rate * facility.total_seats))
        timestamp = start_time + timedelta(minutes=index * interval_minutes)
        points.append(
            ScenarioPoint(
                timestamp=timestamp,
                people_count=people_count,
                temperature=round(21.8 + progress * 0.6, 2),
                humidity=round(39.0 + progress * 1.5, 2),
                power_kw=round(13.8 + progress * 1.8, 2),
                door_count=max(1, round(3 + occupancy_rate * 10)),
                noise_level=round(38.0 + occupancy_rate * 10.0, 2),
            )
        )
    return points


def _telemetry_outage_points(facility: Facility, hours: int, interval_minutes: int) -> list[ScenarioPoint]:
    total_points = max(int((hours * 60) / interval_minutes), 1)
    start_time = utc_now() - timedelta(hours=hours + 2)
    points: list[ScenarioPoint] = []
    for index in range(total_points):
        progress = _scenario_progress(index, total_points)
        occupancy_rate = 0.25 + math.sin(progress * math.pi) * 0.12
        people_count = max(0, round(occupancy_rate * facility.total_seats))
        timestamp = start_time + timedelta(minutes=index * interval_minutes)
        points.append(
            ScenarioPoint(
                timestamp=timestamp,
                people_count=people_count,
                temperature=round(21.4 + occupancy_rate * 1.6, 2),
                humidity=round(40.0 + occupancy_rate * 4.0, 2),
                power_kw=round(7.4 + occupancy_rate * 3.5, 2),
                door_count=max(1, round(4 + occupancy_rate * 12)),
                noise_level=round(41.0 + occupancy_rate * 10.0, 2),
                create_sensor=True,
            )
        )
    return points


def generate_scenario_points(scenario: str, facility: Facility, hours: int, interval_minutes: int) -> list[ScenarioPoint]:
    if scenario == "exam_week_congestion":
        return _exam_week_congestion_points(facility, hours, interval_minutes)
    if scenario == "low_occupancy_energy_waste":
        return _low_occupancy_energy_waste_points(facility, hours, interval_minutes)
    if scenario == "telemetry_outage":
        return _telemetry_outage_points(facility, hours, interval_minutes)
    if scenario == "normal_day":
        return _normal_day_points(facility, hours, interval_minutes)
    raise ValueError(f"Unknown scenario: {scenario}")


def clear_existing_demo_data(db, facility_id: int) -> None:
    db.execute(delete(OccupancyLog).where(OccupancyLog.facility_id == facility_id, OccupancyLog.source_type == "demo_scenario"))
    db.execute(delete(SensorLog).where(SensorLog.facility_id == facility_id, SensorLog.source_type == "demo_scenario"))
    db.execute(delete(FacilityOperationalRollup).where(FacilityOperationalRollup.facility_id == facility_id))
    db.execute(delete(Alert).where(Alert.facility_id == facility_id))
    db.flush()


def apply_scenario(
    *,
    scenario: str,
    facility_id: int | None = None,
    hours: int = 8,
    interval_minutes: int = 15,
    clear_existing: bool = False,
    compute_rollups: bool = False,
    refresh_alerts: bool = False,
) -> dict[str, int]:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")

    db = SessionLocal()
    try:
        facilities_stmt = select(Facility).order_by(Facility.id)
        if facility_id is not None:
            facilities_stmt = facilities_stmt.where(Facility.id == facility_id)
        facilities = list(db.scalars(facilities_stmt).all())

        if not facilities:
            raise ValueError("No matching facilities found for the requested scenario run.")

        occupancy_logs_created = 0
        sensor_logs_created = 0
        rollups_created = 0

        for facility in facilities:
            if clear_existing:
                clear_existing_demo_data(db, facility.id)

            points = generate_scenario_points(scenario, facility, hours, interval_minutes)
            for point in points:
                congestion = calculate_congestion(point.people_count, facility.total_seats, facility.seat_usage_factor)
                create_occupancy_log(
                    db,
                    facility_id=facility.id,
                    timestamp=point.timestamp,
                    people_count=congestion.people_count,
                    occupied_seats=congestion.occupied_seats,
                    available_seats=congestion.available_seats,
                    occupancy_rate=congestion.occupancy_rate,
                    congestion_score=congestion.congestion_score,
                    congestion_level=congestion.congestion_level,
                    confidence=0.89,
                    source_type="demo_scenario",
                )
                occupancy_logs_created += 1

                if point.create_sensor:
                    create_sensor_log(
                        db,
                        facility_id=facility.id,
                        timestamp=point.timestamp,
                        temperature=point.temperature,
                        humidity=point.humidity,
                        power_kw=point.power_kw,
                        door_count=point.door_count,
                        noise_level=point.noise_level,
                        source_type="demo_scenario",
                    )
                    sensor_logs_created += 1

            if compute_rollups:
                compute_and_store_rollup(db, facility.id, window_minutes=max(interval_minutes * 4, 60), dedupe=False)
                rollups_created += 1

            if refresh_alerts:
                sync_operational_alerts(db, facility.id)

        db.commit()
        return {
            "facilities": len(facilities),
            "occupancy_logs_created": occupancy_logs_created,
            "sensor_logs_created": sensor_logs_created,
            "rollups_created": rollups_created,
        }
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate scenario-based demo data for facility operations dashboards.")
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    parser.add_argument("--facility-id", type=int, default=None)
    parser.add_argument("--hours", type=int, default=8)
    parser.add_argument("--interval-minutes", type=int, default=15)
    parser.add_argument("--clear-existing", action="store_true")
    parser.add_argument("--compute-rollups", action="store_true")
    parser.add_argument("--refresh-alerts", action="store_true")
    args = parser.parse_args()

    result = apply_scenario(
        scenario=args.scenario,
        facility_id=args.facility_id,
        hours=max(args.hours, 1),
        interval_minutes=max(args.interval_minutes, 5),
        clear_existing=args.clear_existing,
        compute_rollups=args.compute_rollups,
        refresh_alerts=args.refresh_alerts,
    )
    print(
        "[demo-scenario] "
        f"scenario={args.scenario} facilities={result['facilities']} "
        f"occupancy_logs={result['occupancy_logs_created']} "
        f"sensor_logs={result['sensor_logs_created']} "
        f"rollups={result['rollups_created']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
