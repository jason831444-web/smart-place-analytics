import pytest

from app.services.mqtt_sensors import MqttSensorPayloadError, parse_mqtt_sensor_message, parse_mqtt_sensor_topic


def test_parse_valid_mqtt_sensor_message() -> None:
    message = parse_mqtt_sensor_message(
        "smart-place/facilities/4/sensors",
        """
        {
          "timestamp": "2026-05-18T15:00:00Z",
          "temperature": 22.4,
          "humidity": 42.0,
          "power_kw": 10.8,
          "door_count": 14,
          "noise_level": 51.2,
          "source_type": "publisher"
        }
        """,
    )

    assert message.facility_id == 4
    assert message.temperature == 22.4
    assert message.humidity == 42.0
    assert message.power_kw == 10.8
    assert message.door_count == 14
    assert message.noise_level == 51.2
    assert message.source_type == "mqtt"


def test_reject_invalid_topic_format() -> None:
    with pytest.raises(MqttSensorPayloadError, match="topic must match"):
        parse_mqtt_sensor_topic("smart-place/facility/4/sensors")


def test_reject_invalid_json_payload() -> None:
    with pytest.raises(MqttSensorPayloadError, match="valid JSON"):
        parse_mqtt_sensor_message("smart-place/facilities/1/sensors", "{not json}")


def test_reject_missing_required_numeric_field() -> None:
    with pytest.raises(MqttSensorPayloadError, match="power_kw is required"):
        parse_mqtt_sensor_message(
            "smart-place/facilities/1/sensors",
            """
            {
              "temperature": 22.4,
              "humidity": 42.0,
              "door_count": 14,
              "noise_level": 51.2
            }
            """,
        )


def test_source_type_is_normalized_to_mqtt_when_timestamp_missing() -> None:
    message = parse_mqtt_sensor_message(
        "smart-place/facilities/2/sensors",
        """
        {
          "temperature": 21.9,
          "humidity": 39.5,
          "power_kw": 8.2,
          "door_count": 9,
          "noise_level": 47.1
        }
        """,
    )

    assert message.source_type == "mqtt"
    assert message.timestamp is not None
