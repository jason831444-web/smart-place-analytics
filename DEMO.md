# Demo Guide

This guide is designed for a short recruiter or interviewer walkthrough. The goal is to show the project as an operations analytics platform, not just a CV demo.

## 2-minute demo flow

1. Open the home page and explain the product scope:
   - occupancy analysis
   - telemetry ingestion
   - rollups
   - forecasting
   - recommendations
   - operational alerts

2. Open a facility detail page:
   - point out occupancy metrics
   - show the history chart
   - show sensor and energy signals
   - show forecast and recommendation cards
   - highlight the Operations Pipeline health card

3. Open the live monitoring page:
   - start the webcam
   - explain frame-based analysis every 3 seconds
   - mention persisted occupancy logs and throttled storage behavior

4. Show background jobs:
   - explain synthetic telemetry generation
   - explain rollup creation
   - explain `JobRun` audit trail and operational alerts

5. If time allows, show optional MQTT:
   - publisher -> broker -> subscriber -> `SensorLog` persistence
   - refresh the facility page and point out sensor activity

## Start the app

### Docker

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics
docker compose up --build
```

### Local backend

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

### Local frontend

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics/frontend
npm install
cp .env.example .env.local
npm run dev
```

## Seed data

Seed data is already applied in the Docker backend command. For local backend runs:

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics/backend
python -m app.db.seed
```

Demo admin:

- Email: `admin@example.com`
- Password: `admin12345`

## Run background jobs

### Docker profile

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics
docker compose --profile operations up --build
```

### Local script

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics/backend
python scripts/run_operations_jobs.py --interval-seconds 30 --iterations 0 --generate-sensors --compute-rollups
```

What to point out:

- recurring telemetry generation
- rollup creation
- `JobRun` audit rows
- operations alerts and stale/healthy status

## Run MQTT demo

### Docker profile

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics
docker compose --profile mqtt up --build
```

### Local subscriber

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics/backend
python scripts/subscribe_sensor_mqtt.py --host localhost --port 1883
```

### Local publisher

```bash
cd /Users/yoonjaeseong/Desktop/projects/smart_place_analytics/backend
python scripts/publish_sensor_mqtt.py --host localhost --port 1883 --facility-id 1 --interval-seconds 5 --iterations 0
```

What to point out:

- structured topic parsing
- JSON validation
- broker/subscriber separation
- persisted `SensorLog` records using the same analytics pipeline as the simulator

## Pages to open

- Home: [http://localhost:3000](http://localhost:3000)
- Facilities list: [http://localhost:3000/facilities](http://localhost:3000/facilities)
- Facility detail example: [http://localhost:3000/facilities/1](http://localhost:3000/facilities/1)
- Live monitor example: [http://localhost:3000/facilities/1/live](http://localhost:3000/facilities/1/live)
- Admin login: [http://localhost:3000/admin/login](http://localhost:3000/admin/login)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## What to emphasize in an interview

- This is not just a CV endpoint; it is a full operations analytics workflow
- The app supports multiple ingestion modes: upload, live webcam, background simulation, and optional MQTT
- Time-series persistence powers history, rollups, alerts, forecasting, and recommendations
- Background jobs and `JobRun` audit trails make the pipeline observable
- The architecture is modular and intentionally replaceable: detector backend, telemetry path, forecast logic, and alert logic can all evolve independently

## Good talking points

- Why mock-by-default CV is useful for local reliability
- Why MQTT is optional rather than forced into the default startup path
- Why rollups and alerts make the system feel operational instead of purely analytical
- How the project can evolve toward RTSP, cloud IoT, and stronger forecasting

## Common troubleshooting

- If the frontend loads but data is missing, confirm the backend is running on port `8000`
- If Docker is running but seeded data is not visible, restart the backend service so migrations and seed steps rerun
- If live monitoring fails, confirm browser camera permissions are allowed
- If MQTT publisher cannot send messages, confirm Mosquitto is running on port `1883`
- If MQTT subscriber rejects messages, check the topic format:
  - `smart-place/facilities/{facility_id}/sensors`
- If YOLO mode is enabled and model load fails, switch back to `CV_BACKEND=mock`

## Suggested screenshot capture list

- facility dashboard overview
- live monitoring page while analyzing frames
- Operations Pipeline card with alert state
- MQTT publisher/subscriber terminal output
- admin overview or facility management page
