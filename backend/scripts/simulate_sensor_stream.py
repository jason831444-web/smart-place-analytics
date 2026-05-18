import argparse
import random
import time
from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Facility
from app.services.operations import latest_status
from app.services.sensors import create_sensor_log


def simulated_payload(facility: Facility, occupancy_rate: float) -> dict:
    occupancy_scale = max(0.0, min(occupancy_rate, 1.0))
    base_temp = 21.5 + random.uniform(-1.2, 1.8)
    return {
        "temperature": round(base_temp + occupancy_scale * 2.4, 2),
        "humidity": round(40 + occupancy_scale * 10 + random.uniform(-4, 4), 2),
        "power_kw": round(6 + occupancy_scale * 8 + random.uniform(-1.2, 1.2), 2),
        "door_count": max(0, int((facility.total_seats * 0.15) * occupancy_scale + random.randint(0, 6))),
        "noise_level": round(42 + occupancy_scale * 24 + random.uniform(-3, 5), 2),
    }


def run(interval_seconds: int, iterations: int | None) -> None:
    count = 0
    while iterations is None or count < iterations:
        db = SessionLocal()
        try:
            facilities = list(db.scalars(select(Facility).order_by(Facility.id)).all())
            for facility in facilities:
                status = latest_status(db, facility.id)
                payload = simulated_payload(facility, status.occupancy_rate)
                create_sensor_log(
                    db,
                    facility_id=facility.id,
                    timestamp=datetime.utcnow(),
                    source_type="simulator",
                    **payload,
                )
            db.commit()
        finally:
            db.close()

        count += 1
        if iterations is None or count < iterations:
            time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate facility sensor telemetry.")
    parser.add_argument("--interval-seconds", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=12, help="Set to 0 to run indefinitely.")
    args = parser.parse_args()
    run(interval_seconds=max(args.interval_seconds, 1), iterations=None if args.iterations == 0 else max(args.iterations, 1))


if __name__ == "__main__":
    main()
