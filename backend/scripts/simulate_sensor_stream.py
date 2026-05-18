import argparse
import time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Facility
from app.services.operations import latest_status
from app.services.sensors import create_sensor_log, simulated_sensor_payload
from app.utils.time import utc_now


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
                    timestamp=utc_now(),
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
