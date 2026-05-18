import argparse
import json
import time

from app.db.session import SessionLocal
from app.models import Facility
from app.services.operations import latest_status
from app.services.sensors import simulated_sensor_payload
from app.utils.time import utc_now


def build_payload(facility_id: int) -> dict[str, object]:
    db = SessionLocal()
    try:
        facility = db.get(Facility, facility_id)
        if facility is None:
            raise ValueError(f"Facility {facility_id} does not exist")
        status = latest_status(db, facility_id)
        payload = simulated_sensor_payload(facility, status.occupancy_rate)
        payload["timestamp"] = utc_now().isoformat() + "Z"
        payload["source_type"] = "mqtt"
        return payload
    finally:
        db.close()


def run(host: str, port: int, facility_id: int, interval_seconds: int, iterations: int) -> None:
    import paho.mqtt.client as mqtt

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(host, port, keepalive=60)
    client.loop_start()

    topic = f"smart-place/facilities/{facility_id}/sensors"
    count = 0

    try:
        while iterations == 0 or count < iterations:
            payload = build_payload(facility_id)
            message = json.dumps(payload)
            client.publish(topic, message)
            print(f"[mqtt-publisher] published {topic} {message}", flush=True)

            count += 1
            if iterations == 0 or count < iterations:
                time.sleep(max(interval_seconds, 1))
    except KeyboardInterrupt:
        return
    finally:
        client.loop_stop()
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish synthetic sensor telemetry to MQTT.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--facility-id", type=int, default=1)
    parser.add_argument("--interval-seconds", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=0, help="Use 0 to run forever.")
    args = parser.parse_args()

    run(
        host=args.host,
        port=args.port,
        facility_id=max(args.facility_id, 1),
        interval_seconds=max(args.interval_seconds, 1),
        iterations=max(args.iterations, 0),
    )


if __name__ == "__main__":
    main()
