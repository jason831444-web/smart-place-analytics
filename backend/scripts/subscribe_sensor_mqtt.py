import argparse

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Facility
from app.services.alerts import sync_operational_alerts
from app.services.mqtt_sensors import MqttSensorPayloadError, parse_mqtt_sensor_message
from app.services.sensors import create_sensor_log


def persist_message(db: Session, topic: str, payload: bytes) -> str:
    message = parse_mqtt_sensor_message(topic, payload)
    facility = db.get(Facility, message.facility_id)
    if facility is None:
        raise MqttSensorPayloadError(f"Facility {message.facility_id} does not exist")

    create_sensor_log(
        db,
        facility_id=message.facility_id,
        timestamp=message.timestamp,
        temperature=message.temperature,
        humidity=message.humidity,
        power_kw=message.power_kw,
        door_count=message.door_count,
        noise_level=message.noise_level,
        source_type=message.source_type,
    )
    sync_operational_alerts(db, message.facility_id)
    db.commit()
    return (
        f"[mqtt-subscriber] ingested facility={message.facility_id} "
        f"power_kw={message.power_kw:.1f} temperature={message.temperature:.1f}"
    )


def run(host: str, port: int) -> None:
    import paho.mqtt.client as mqtt

    def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties) -> None:  # type: ignore[override]
        client.subscribe("smart-place/facilities/+/sensors")
        print(f"[mqtt-subscriber] subscribed to smart-place/facilities/+/sensors on {host}:{port}", flush=True)

    def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:  # type: ignore[override]
        db = SessionLocal()
        try:
            line = persist_message(db, msg.topic, msg.payload)
            print(line, flush=True)
        except Exception as exc:
            db.rollback()
            print(f"[mqtt-subscriber] skipped topic={msg.topic}: {exc}", flush=True)
        finally:
            db.close()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscribe to MQTT sensor telemetry and persist SensorLog rows.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
