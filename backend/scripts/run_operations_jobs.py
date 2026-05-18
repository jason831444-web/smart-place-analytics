import argparse

from app.services.job_runner import run_loop


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lightweight background operations jobs.")
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--facility-id", type=int, default=None)
    parser.add_argument("--iterations", type=int, default=12, help="Use 0 to run forever.")
    parser.add_argument("--window-minutes", type=int, default=60)
    parser.add_argument("--compute-rollups", action="store_true")
    parser.add_argument("--generate-sensors", action="store_true")
    args = parser.parse_args()

    generate_sensors = args.generate_sensors or not args.compute_rollups
    compute_rollups = args.compute_rollups or not args.generate_sensors

    run_loop(
        interval_seconds=max(args.interval_seconds, 1),
        facility_id=args.facility_id,
        iterations=args.iterations,
        generate_sensors=generate_sensors,
        compute_rollups=compute_rollups,
        window_minutes=max(args.window_minutes, 15),
    )


if __name__ == "__main__":
    main()
