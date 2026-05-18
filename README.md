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
    -> forecasting service
    -> recommendation engine
    -> PostgreSQL
    -> local media storage

Optional simulator:
  sensor simulator script
    -> SensorLog ingestion
    -> PostgreSQL
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

Optional sensor simulator:

```bash
cd backend
python scripts/simulate_sensor_stream.py --interval-seconds 5 --iterations 0
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

## Current Limitations

- Seat occupancy is still derived from detected people and facility capacity, not a true seat-level classifier.
- Live monitoring is browser-webcam snapshot polling rather than RTSP/CCTV ingestion.
- Sensor ingestion is currently a simulator script, not a full MQTT deployment.
- Forecasting is baseline statistical logic, not a trained ML model.
- Recommendation generation is rule-based and deterministic.

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
