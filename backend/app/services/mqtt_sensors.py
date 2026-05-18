import json
from dataclasses import dataclass
from datetime import datetime

from app.utils.time import utc_now

MQTT_SENSOR_TOPIC_PREFIX = "smart-place/facilities/"
MQTT_SENSOR_TOPIC_SUFFIX = "/sensors"


class MqttSensorPayloadError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedMqttSensorMessage:
    facility_id: int
    timestamp: datetime
    temperature: float
    humidity: float
    power_kw: float
    door_count: int
    noise_level: float
    source_type: str


def _parse_timestamp(raw_timestamp: object) -> datetime:
    if raw_timestamp is None:
        return utc_now()
    if not isinstance(raw_timestamp, str) or not raw_timestamp.strip():
        raise MqttSensorPayloadError("timestamp must be an ISO 8601 string when provided")

    normalized = raw_timestamp.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise MqttSensorPayloadError("timestamp must be a valid ISO 8601 string") from exc

    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def parse_mqtt_sensor_topic(topic: str) -> int:
    if not topic.startswith(MQTT_SENSOR_TOPIC_PREFIX) or not topic.endswith(MQTT_SENSOR_TOPIC_SUFFIX):
        raise MqttSensorPayloadError("topic must match smart-place/facilities/{facility_id}/sensors")

    facility_segment = topic[len(MQTT_SENSOR_TOPIC_PREFIX) : -len(MQTT_SENSOR_TOPIC_SUFFIX)]
    if "/" in facility_segment or not facility_segment.isdigit():
        raise MqttSensorPayloadError("facility_id in topic must be a positive integer")

    facility_id = int(facility_segment)
    if facility_id <= 0:
        raise MqttSensorPayloadError("facility_id in topic must be a positive integer")
    return facility_id


def parse_mqtt_sensor_message(topic: str, payload: bytes | str) -> ParsedMqttSensorMessage:
    facility_id = parse_mqtt_sensor_topic(topic)
    raw_payload = payload.decode("utf-8") if isinstance(payload, bytes) else payload

    try:
        document = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise MqttSensorPayloadError("payload must be valid JSON") from exc

    if not isinstance(document, dict):
        raise MqttSensorPayloadError("payload must be a JSON object")

    required_fields = {
        "temperature": float,
        "humidity": float,
        "power_kw": float,
        "door_count": int,
        "noise_level": float,
    }

    parsed_values: dict[str, float | int] = {}
    for field_name, numeric_type in required_fields.items():
        if field_name not in document:
            raise MqttSensorPayloadError(f"{field_name} is required")

        raw_value = document[field_name]
        if isinstance(raw_value, bool):
            raise MqttSensorPayloadError(f"{field_name} must be numeric")

        try:
            parsed_values[field_name] = int(raw_value) if numeric_type is int else float(raw_value)
        except (TypeError, ValueError) as exc:
            raise MqttSensorPayloadError(f"{field_name} must be numeric") from exc

    return ParsedMqttSensorMessage(
        facility_id=facility_id,
        timestamp=_parse_timestamp(document.get("timestamp")),
        temperature=float(parsed_values["temperature"]),
        humidity=float(parsed_values["humidity"]),
        power_kw=float(parsed_values["power_kw"]),
        door_count=int(parsed_values["door_count"]),
        noise_level=float(parsed_values["noise_level"]),
        source_type="mqtt",
    )
