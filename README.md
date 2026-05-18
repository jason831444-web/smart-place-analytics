# Smart Place Analytics

Smart Place Analytics is a real-time facility operations analytics platform for libraries, lounges, study rooms, cafes, and shared spaces. It combines computer-vision occupancy analysis, time-series telemetry, near-term forecasting, and rule-based operational recommendations in a single full-stack system built for local demos and portfolio presentation.

The project keeps the original upload-and-analyze workflow, then extends it toward a more industrial operations story:

- real-time webcam-driven occupancy ingestion
- persistent occupancy and sensor time-series logs
- facility summary and historical analytics
- near-term occupancy forecasting
- recommendation generation for congestion and energy efficiency
- production-minded local development with Docker, migrations, seed data, tests, and CI

## Platform Positioning

Smart Place Analytics is now aimed at the same class of problems you would see in an industrial facility operations product:

- real-time data ingestion from computer vision and synthetic telemetry
- time-series analytics for occupancy and environmental signals
- operational dashboards for utilization, congestion, and energy
- forecasting APIs for short-horizon planning
- recommendation APIs that turn analytics into action

## Architecture Summary

```text
Browser / Next.js UI
  -> FastAPI REST API
    -> CV analysis service (mock or YOLO)
    -> occupancy time-series service
    -> sensor telemetry service
    -> operational rollup service
    -> forecasting service
    -> recommendation engine
    -> PostgreSQL
    -> local media storage

Optional background jobs:
  sensor simulator script / operations job runner
    -> SensorLog ingestion
    -> FacilityOperationalRollup generation
    -> JobRun audit trail
    -> Operational alert refresh
    -> PostgreSQL

Optional MQTT demo path:
  MQTT publisher
    -> Mosquitto broker
    -> MQTT subscriber
    -> SensorLog ingestion
    -> existing rollups / alerts / dashboards
```

## Core Features

- Public facility list with current status cards
- Facility detail page with:
  - current occupancy metrics
  - historical occupancy chart
  - image upload analysis
  - sensor and energy chart
  - forecast card
  - recommendation feed
  - alert-style high congestion indicators
- Live monitoring page with webcam capture every 3 seconds
- Admin dashboard and facility management
- Time-series occupancy logging for upload-driven and live analysis flows
- Synthetic sensor telemetry simulator for industrial IoT-style demos
- Optional MQTT-based telemetry ingestion for industrial IoT-style demos
- Forecasting endpoint using moving-average and same-hour historical baselines
- Recommendation engine for congestion, overflow, staffing, and energy actions

## Tech Stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts
- Backend: FastAPI, Pydantic, SQLAlchemy 2, Alembic
- Database: PostgreSQL
- Auth: JWT bearer tokens
- CV: swappable detector interface with deterministic mock fallback and YOLO-ready option
- Storage: local upload and annotated image storage
- Tooling: Docker Compose, pytest, GitHub Actions

## Current Architecture Audit

Before this extension, the application already had:

- facility metadata stored in `facilities`
- uploaded images stored in `uploads`
- analysis results stored in `analyses`
- historical occupancy snapshots stored in `occupancy_logs`
- public routes for facility list, detail, status, and history
- admin routes for facility CRUD and analytics overview
- a webcam-based live page that reused the CV pipeline

The existing persistence path was:

```text
upload/live frame
  -> detector
  -> congestion calculation
  -> analyses row
  -> occupancy_logs row
  -> facility detail/admin analytics
```

This upgrade keeps that flow and enriches it with:

- richer occupancy log metadata
- sensor telemetry ingestion
- forecast generation
- recommendation generation
- expanded facility dashboards

## Data Model

### Existing

- `users`
- `facilities`
- `uploads`
- `analyses`
- `occupancy_logs`
- `alerts`

### Added / Extended

#### `occupancy_logs`

The occupancy log model now captures richer time-series metadata:

- `id`
- `facility_id`
- `analysis_id` nullable
- `timestamp`
- `people_count`
- `occupied_seats`
- `available_seats`
- `occupancy_rate`
- `congestion_score`
- `congestion_level`
- `confidence`
- `source_type`
- `image_path`
- `annotated_image_path`
- `created_at`

This allows both persisted upload analyses and transient live webcam analyses to contribute time-series records.

#### `sensor_logs`

- `id`
- `facility_id`
- `timestamp`
- `temperature`
- `humidity`
- `power_kw`
- `door_count`
- `noise_level`
- `source_type`
- `created_at`

#### `facility_operational_rollups`

- `id`
- `facility_id`
- `timestamp`
- `window_minutes`
- `avg_occupancy_rate`
- `peak_occupancy_rate`
- `high_congestion_events`
- `avg_power_kw` nullable
- `peak_power_kw` nullable
- `avg_temperature` nullable
- `avg_noise_level` nullable
- `recommendation_count`
- `created_at`

#### `job_runs`

- `id`
- `job_name`
- `status`
- `started_at`
- `finished_at`
- `duration_ms`
- `facilities_processed`
- `sensors_generated`
- `rollups_computed`
- `error_message` nullable
- `created_at`

#### `alerts`

The alert model is extended for lightweight operational observability:

- `facility_id`
- `alert_type`
- `severity`
- `title`
- `threshold`
- `message`
- `evidence_json`
- `status`
- `triggered_at`

## Local Setup With Docker

Prerequisites:

- Docker Desktop

Run the full stack:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Demo admin account:

- Email: `admin@example.com`
- Password: `admin12345`

Run the optional synthetic sensor simulator service:

```bash
docker compose --profile simulator up --build
```

Run the optional operations job runner service:

```bash
docker compose --profile operations up --build
```

Run the optional MQTT demo stack:

```bash
docker compose --profile mqtt up --build
```

## Local Setup Without Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend production validation:

```bash
cd frontend
npm run build
```

The frontend `build` script uses the Webpack build path for compatibility with the current local setup.

Optional sensor simulator:

```bash
cd backend
python scripts/simulate_sensor_stream.py --interval-seconds 5 --iterations 0
```

Optional operations job runner:

```bash
cd backend
python scripts/run_operations_jobs.py --interval-seconds 30 --iterations 0 --generate-sensors --compute-rollups
```

Optional MQTT publisher and subscriber:

```bash
cd backend
python scripts/subscribe_sensor_mqtt.py --host localhost --port 1883
```

```bash
cd backend
python scripts/publish_sensor_mqtt.py --host localhost --port 1883 --facility-id 1 --interval-seconds 5 --iterations 0
```

Enable YOLO locally:

```bash
cd backend
pip install -r requirements-ml.txt
CV_BACKEND=yolo YOLO_MODEL=yolov8n.pt uvicorn app.main:app --reload
```

Enable YOLO with Docker:

```bash
BACKEND_REQUIREMENTS_FILE=requirements-ml.txt CV_BACKEND=yolo YOLO_MODEL=yolov8n.pt docker compose up --build
```

## Environment Variables

Backend:

- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `PUBLIC_BASE_URL`
- `STORAGE_DIR`
- `CV_BACKEND`
- `YOLO_MODEL`
- `YOLO_CONFIDENCE_THRESHOLD`
- `YOLO_DEVICE`
- `YOLO_FALLBACK_TO_MOCK`
- `LIVE_PERSIST_INTERVAL_SECONDS`
- `MAX_UPLOAD_BYTES`
- `MAX_LIVE_FRAME_BYTES`
- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`
- `INTERNAL_API_BASE_URL`

## Database Migrations

Run migrations:

```bash
cd backend
alembic upgrade head
```

Create a new migration:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

## Real-Time Occupancy Ingestion

### Upload Analysis

1. A user uploads an image for a facility.
2. The backend validates and stores the image.
3. The configured detector estimates people count.
4. Congestion metrics are calculated from people count and capacity.
5. The system stores:
   - `uploads`
   - `analyses`
   - `occupancy_logs`

### Live Monitoring

The live page is available at:

- `/facilities/{facility_id}/live`

How it works:

1. The browser requests webcam access with `getUserMedia`.
2. The page captures a frame every 3 seconds.
3. The frame is sent to `POST /api/live/analyze`.
4. The backend reuses the same detector and congestion logic as uploads.
5. Every live request produces a structured occupancy response.
6. Occupancy logs are created for live samples.
7. Full upload + analysis persistence still follows the existing throttled interval to avoid storing every frame as a heavy media artifact.

This keeps the platform near-real-time without overwhelming the database or storage layer.

Data conventions:

- `occupancy_rate` is stored and returned as a `0.0-1.0` fraction and rendered as a percentage in the frontend.
- `confidence` is stored and returned as a `0.0-1.0` score.
- `congestion_level` values are `Low`, `Medium`, and `High`.
- Occupancy `source_type` values normalize to `image_upload` or `webcam`.
- Sensor `source_type` values normalize to `simulator`.

## Sensor Simulation

The first industrial telemetry step is a synthetic sensor stream rather than MQTT-first complexity.

The simulator writes `sensor_logs` for each facility with:

- temperature
- humidity
- power draw in kW
- door count
- noise level

The simulator is implemented as:

- `backend/scripts/simulate_sensor_stream.py`

This keeps the architecture ready for a future MQTT broker or stream consumer while remaining easy to run locally today.

## MQTT Telemetry Ingestion

MQTT is an optional local demo path that layers onto the existing sensor architecture without replacing the simulator or background jobs.

The MQTT flow is:

```text
synthetic MQTT publisher
  -> Mosquitto broker
  -> MQTT subscriber
  -> SensorLog persistence
  -> existing rollups, alerts, and dashboards
```

Topic format:

- `smart-place/facilities/{facility_id}/sensors`

Example payload:

```json
{
  "timestamp": "2026-05-18T15:00:00Z",
  "temperature": 22.4,
  "humidity": 42.0,
  "power_kw": 10.8,
  "door_count": 14,
  "noise_level": 51.2,
  "source_type": "mqtt"
}
```

Files:

- `backend/app/services/mqtt_sensors.py`
- `backend/scripts/publish_sensor_mqtt.py`
- `backend/scripts/subscribe_sensor_mqtt.py`

Verification path after messages are ingested:

- `GET /api/facilities/{facility_id}/sensor-logs`
- `GET /api/operations/job-status`
- facility detail dashboard `Operations Pipeline` card

## Operational Rollups

Rollups live in:

- `backend/app/services/rollups.py`

The rollup layer computes periodic facility summaries over a configurable time window, with a default of 60 minutes.

Each rollup stores:

- average occupancy rate
- peak occupancy rate
- number of high congestion events
- average and peak power draw when sensor data exists
- average temperature and noise level when sensor data exists
- recommendation count at rollup time

Rollups are safe when sensor data is missing. Those sensor-derived fields remain nullable rather than failing the computation.

To avoid excessive duplication in local demo mode, rollups deduplicate within a short time window when repeated with the same `window_minutes` value.

## Background Jobs

The platform now includes a lightweight background operations pipeline for local demos and interview walkthroughs.

Job runner:

- `backend/scripts/run_operations_jobs.py`

Supported behaviors:

- generate synthetic sensor logs for facilities
- compute facility operational rollups
- record a `job_runs` audit row for every iteration
- refresh operational alerts for each successfully processed facility
- target one facility or all facilities
- run once, a fixed number of iterations, or forever

Example commands:

```bash
cd backend
python scripts/run_operations_jobs.py --interval-seconds 30 --iterations 10 --generate-sensors --compute-rollups
```

```bash
cd backend
python scripts/run_operations_jobs.py --facility-id 1 --interval-seconds 15 --iterations 0 --compute-rollups
```

The purpose is to demonstrate scheduled operational data pipelines in addition to request/response analytics.

## Job Audit Trail

Every background job iteration now records a `job_runs` row with:

- start and finish time
- duration in milliseconds
- facilities successfully processed
- number of sensor logs generated
- number of rollups computed
- final job status: `success`, `partial`, or `failed`
- aggregated error details when something goes wrong

This makes it easy to answer:

- when the pipeline last ran
- whether the last run completed successfully
- whether some facilities failed while others still succeeded

## Operational Alerts

Operational alerts are generated from current facility state and refreshed by both the background runner and operations endpoints.

Current alert types:

- `stale_telemetry`
- `overdue_rollup`
- `high_congestion`
- `energy_mismatch`

These alerts make the platform observable in a practical way without introducing a heavyweight incident system.

## Forecasting

Forecasting lives in:

- `backend/app/services/forecasting.py`

The baseline method is intentionally simple and replaceable:

- moving average of recent occupancy samples
- same-hour historical average when enough data exists
- hybrid blending when both are available

Response includes:

- predicted occupancy rate
- predicted congestion level
- confidence
- method
- explanation

## Recommendation Engine

Recommendations live in:

- `backend/app/services/recommendations.py`

Current rules cover:

- redirecting users when occupancy is already high
- preparing overflow capacity when forecast occupancy is too high
- reducing energy usage when power draw is high but occupancy is low
- suggesting staffing or schedule review when high congestion repeats

## API Summary

### Public / user-facing

- `GET /api/facilities`
- `GET /api/facilities/{facility_id}`
- `GET /api/facilities/{facility_id}/status`
- `GET /api/facilities/{facility_id}/history`
- `GET /api/facilities/{facility_id}/occupancy-logs`
- `GET /api/facilities/{facility_id}/latest-status`
- `GET /api/facilities/{facility_id}/summary`
- `GET /api/facilities/{facility_id}/sensor-logs`
- `GET /api/facilities/{facility_id}/sensor-summary`
- `GET /api/facilities/{facility_id}/rollups`
- `GET /api/facilities/{facility_id}/rollups/latest`
- `GET /api/facilities/{facility_id}/operations-alerts`
- `GET /api/facilities/{facility_id}/forecast?window_minutes=60`
- `GET /api/facilities/{facility_id}/recommendations`
- `POST /api/uploads`
- `POST /api/uploads/analyze`
- `GET /api/analyses/{analysis_id}`

### Live

- `POST /api/live/analyze`

### Admin

- `POST /api/auth/login`
- `GET /api/admin/facilities`
- `POST /api/admin/facilities`
- `PUT /api/admin/facilities/{facility_id}`
- `DELETE /api/admin/facilities/{facility_id}`
- `GET /api/admin/analytics/overview`
- `GET /api/admin/analytics/facilities/{facility_id}`
- `POST /api/facilities/{facility_id}/rollups/compute`

### Operations pipeline

- `GET /api/operations/job-status`
- `GET /api/operations/job-runs`
- `GET /api/operations/alerts`

## UI Overview

The facility detail dashboard now includes:

- live status card
- occupancy history chart
- sensor and energy chart
- forecast card
- recommendation feed
- high congestion event visibility
- system status indicator

The live page includes:

- camera preview
- real-time occupancy metrics
- last updated state
- last submitted or annotated frame
- forecast card
- recommendations

## Screenshots / GIF Placeholders

Add media here after running locally:

- facility overview dashboard
- facility detail analytics dashboard
- live monitoring page
- admin overview
- sensor telemetry chart
- recommendation cards

## Testing

Backend tests:

```bash
cd backend
pytest
```

Frontend validation:

```bash
cd frontend
npm run lint
npm run build
```

CI:

- `.github/workflows/ci.yml`
- runs backend tests
- builds the frontend

## Security and Reliability Notes

- Uploaded images and live frames are validated as real JPEG, PNG, or WebP images.
- Live analysis requires an admin token.
- Error handling avoids surfacing raw backend internals in the UI.
- The default Docker path remains lightweight with the mock detector.
- YOLO remains opt-in through `requirements-ml.txt` and `CV_BACKEND=yolo`.
- Background jobs use a simple loop-and-sleep runner rather than a distributed queue for the MVP.
- Operations endpoints refresh alert state on read so the dashboard reflects current stale or overdue conditions.
- MQTT ingestion is optional and only activates when you run the broker and subscriber.

## Current Limitations

- Seat occupancy is still derived from detected people and facility capacity, not a true seat-level classifier.
- Live monitoring is browser-webcam snapshot polling rather than RTSP/CCTV ingestion.
- Sensor ingestion is currently a simulator script, not a full MQTT deployment.
- MQTT is an optional local-demo ingestion path with a local Mosquitto broker.
- Operational rollups are periodic database snapshots rather than materialized views or streaming aggregations.
- Job audit trails are stored in the application database rather than exported to a separate monitoring stack.
- Alerts are lightweight operational signals, not a full incident management workflow with acknowledgements or notifications.
- The local MQTT broker is intentionally unauthenticated and non-TLS for development convenience.
- There is no production message queue, retained-topic strategy, or cloud IoT integration yet.
- Forecasting is baseline statistical logic, not a trained ML model.
- Recommendation generation is rule-based and deterministic.
- MQTT ingestion, ML forecasting, and end-to-end browser tests are planned next steps.

## Future Improvements

- Replace synthetic sensor ingestion with MQTT or stream-based telemetry
- Add RTSP/CCTV workers and server-side sampling
- Add WebSocket or SSE push updates
- Train a stronger forecasting model with scikit-learn or XGBoost
- Add detector health telemetry and model monitoring
- Add export workflows and alert delivery channels
- Add broader role-based access control

## Portfolio Highlights

- Built a real-time facility operations analytics platform using Next.js, FastAPI, PostgreSQL, Docker, and computer vision to monitor occupancy and congestion.
- Designed a time-series analytics pipeline for facility occupancy and sensor data.
- Implemented forecasting and recommendation APIs to predict near-term congestion and suggest operational actions.
- Added live monitoring and production-minded testing workflows.
- Added a lightweight background operations pipeline that periodically generates telemetry and computes facility rollups for time-series monitoring and operational decision support.
- Added job audit trails and operational alerts to track background pipeline health, stale telemetry, overdue rollups, and facility-level operational risks.
- Added optional MQTT-based telemetry ingestion with a local broker, publisher, subscriber, validation layer, and SensorLog persistence to simulate an industrial IoT data pipeline.
