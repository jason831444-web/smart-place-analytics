# Architecture Guide

## System overview

Smart Place Analytics is structured as a modular full-stack operations platform:

- Next.js frontend for dashboards, live monitoring, and admin flows
- FastAPI backend for API routes and application services
- PostgreSQL for durable storage of facility metadata, analyses, time-series logs, rollups, job runs, and alerts
- Local storage for uploaded and annotated images
- Optional Mosquitto + MQTT publisher/subscriber path for telemetry ingestion demos

## Request/response path

### Upload or live analysis

```text
browser upload or webcam frame
  -> FastAPI endpoint
  -> CV detector service
  -> congestion calculation
  -> Analysis + OccupancyLog persistence
  -> facility dashboard / history / forecast / recommendations
```

Key backend areas:

- `backend/app/api/uploads.py`
- `backend/app/api/live.py`
- `backend/app/services/analysis.py`
- `backend/app/services/congestion.py`
- `backend/app/cv/`

## Background pipeline path

```text
run_operations_jobs.py
  -> generate synthetic sensor telemetry
  -> persist SensorLog rows
  -> compute FacilityOperationalRollup rows
  -> refresh operational alerts
  -> persist JobRun audit row
  -> facility dashboard Operations Pipeline card
```

Key backend areas:

- `backend/app/services/job_runner.py`
- `backend/app/services/sensors.py`
- `backend/app/services/rollups.py`
- `backend/app/services/alerts.py`
- `backend/scripts/run_operations_jobs.py`

## MQTT ingestion path

```text
publish_sensor_mqtt.py
  -> Mosquitto broker
  -> subscribe_sensor_mqtt.py
  -> mqtt_sensors parser / validator
  -> SensorLog persistence
  -> existing rollups / alerts / dashboards
```

Key backend areas:

- `backend/app/services/mqtt_sensors.py`
- `backend/scripts/publish_sensor_mqtt.py`
- `backend/scripts/subscribe_sensor_mqtt.py`
- `docker/mosquitto/mosquitto.conf`

## Database model summary

Primary entities:

- `Facility`
- `Upload`
- `Analysis`
- `OccupancyLog`
- `SensorLog`
- `FacilityOperationalRollup`
- `JobRun`
- `Alert`
- `User`

How they fit together:

- `Analysis` stores a specific persisted CV result
- `OccupancyLog` stores time-series occupancy snapshots from upload or live workflows
- `SensorLog` stores environmental and operational telemetry
- `FacilityOperationalRollup` stores periodic summaries derived from logs
- `JobRun` stores audit data for background iterations
- `Alert` stores active or resolved operational issues

## Reliability and observability notes

- Mock CV backend is the default for reliable local startup
- YOLO is available as an opt-in path
- Background jobs create `JobRun` audit entries with success, partial, or failed states
- Operations endpoints expose pipeline freshness and active alert counts
- Rollups and alerts are derived from durable logs rather than transient in-memory state
- MQTT is optional so the default stack stays lightweight

## Why the architecture is easy to explain

- Every major concern has a clear service boundary
- Optional demo paths converge into the same persistence layer
- The system grows from simple request/response analytics into scheduled operations workflows
- The project demonstrates both product thinking and operational reliability

## Limitations

- Forecasting is baseline and intentionally simple
- Alerts are rule-based, not model-driven
- MQTT is a local-demo path, not a production IoT platform
- Live analysis is browser-frame polling, not RTSP/CCTV stream processing
- Job scheduling is loop-and-sleep, not a distributed worker system

## Future production upgrades

- RTSP/CCTV ingestion workers
- richer forecasting models
- alert acknowledgement and notification delivery
- subscriber health telemetry and broker monitoring
- cloud object storage and deployment hardening
- cloud IoT or managed message bus integration
