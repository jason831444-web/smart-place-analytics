# Smart Seat and Facility Congestion Analysis System

An end-to-end full-stack application for estimating facility congestion from uploaded images, storing analysis history, and presenting operational analytics for spaces such as libraries, classrooms, study rooms, and cafes.

This repository is built as a strong MVP/portfolio foundation: FastAPI backend, PostgreSQL persistence, Alembic migrations, a modular computer-vision layer, JWT admin auth, a Next.js dashboard, Docker Compose, seed data, and tests for the core analytics logic.

## Architecture

```mermaid
flowchart LR
  UI["Next.js dashboard"] --> API["FastAPI REST API"]
  API --> DB[("PostgreSQL")]
  API --> Storage["Local file storage"]
  API --> CV["Person detector interface"]
  CV --> Mock["Mock detector fallback"]
  CV --> YOLO["Optional YOLO detector"]
  API --> Analytics["Aggregation services"]
```

## Tech Stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts
- Backend: FastAPI, Pydantic, SQLAlchemy 2, Alembic
- Database: PostgreSQL
- Auth: JWT bearer tokens with bcrypt password hashing
- Storage: local upload and annotated-image directories
- CV: swappable detector interface with deterministic mock fallback and optional YOLO support
- DevOps: Docker Compose for Postgres, backend, and frontend

## Features

- Public facility list with current people count, available seats, occupancy rate, and congestion badge
- Facility detail page with metadata, image, current status, upload-and-analyze flow, annotated result preview, history chart, and recent logs
- Admin login with seeded demo account
- Admin dashboard with summary metrics, busiest facilities ranking, peak-hour chart, and recent system activity
- Admin facility management for create, edit, and delete
- Persistent uploads, analyses, and occupancy logs
- Analytics endpoints for overview, facility history, peak hours, daily trend, and rankings
- Defensive congestion calculation with clamping and zero-seat handling
- Alembic migration and seed/demo data
- Backend unit tests for congestion and analytics helpers

## Screenshots

Add portfolio screenshots here after running locally:

- Home dashboard
- Facility detail with annotated detection preview
- Admin analytics dashboard
- Facility management page

## Local Setup With Docker

Prerequisites:

- Docker Desktop

Run the full stack:

```bash
docker compose up --build
```

The backend container runs migrations and seeds demo data automatically.

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Demo admin account:

- Email: `admin@example.com`
- Password: `admin12345`

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

For non-Docker local backend development, update `backend/.env` so `DATABASE_URL` points to your local PostgreSQL instance.

## Environment Variables

Backend:

- `DATABASE_URL`: SQLAlchemy database URL
- `SECRET_KEY`: JWT signing secret
- `CORS_ORIGINS`: JSON list of allowed frontend origins
- `PUBLIC_BASE_URL`: base URL used for generated media links
- `STORAGE_DIR`: local storage directory
- `CV_BACKEND`: `mock` or `yolo`
- `YOLO_MODEL`: YOLO weights name/path when `CV_BACKEND=yolo`
- `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`: demo admin credentials

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`: API root, typically `http://localhost:8000/api`

## Database Migrations

Run migrations from the backend directory:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

## How Analysis Works

1. A user uploads an image for a facility.
2. The backend saves an `uploads` record and the image file.
3. The analysis service calls the configured `PersonDetector`.
4. The detector returns people count and optional bounding boxes.
5. Occupied seats are estimated as `min(people_count, total_seats)`.
6. `available_seats = max(total_seats - occupied_seats, 0)`.
7. `occupancy_rate = occupied_seats / total_seats`, with zero-seat facilities handled as 0.
8. Congestion level is assigned as:
   - Low: 0.00 to 0.30
   - Medium: 0.31 to 0.70
   - High: 0.71+
9. The backend stores both an `analyses` row and an `occupancy_logs` row.
10. If detections include boxes, an annotated image is generated for display.

The default detector is a deterministic mock so the project runs immediately without downloading model weights. To try YOLO locally, install `backend/requirements-ml.txt`, set `CV_BACKEND=yolo`, and restart the API. The YOLO implementation filters detections to the `person` class and can be replaced without changing route code.

## API Highlights

Public/user:

- `GET /api/facilities`
- `GET /api/facilities/{facility_id}`
- `GET /api/facilities/{facility_id}/status`
- `GET /api/facilities/{facility_id}/history`
- `POST /api/uploads`
- `POST /api/uploads/analyze`
- `POST /api/analyze`
- `GET /api/analyses/{analysis_id}`

Admin:

- `POST /api/auth/login`
- `GET /api/admin/facilities`
- `POST /api/admin/facilities`
- `PUT /api/admin/facilities/{facility_id}`
- `DELETE /api/admin/facilities/{facility_id}`
- `GET /api/admin/analytics/overview`
- `GET /api/admin/analytics/facilities/{facility_id}`

## Testing

Backend tests:

```bash
cd backend
pytest
```

Frontend validation:

```bash
cd frontend
npm run build
```

## Current Limitations

- Seat-level occupancy is estimated from people detection and total capacity; no dedicated seat detector/classifier is included yet.
- Live camera ingestion is intentionally structured for future work but not implemented as a streaming service.
- Local filesystem storage is used for MVP simplicity; cloud object storage can be added behind the storage service.
- The mock detector is deterministic and useful for demos, but not real CV inference.
- Admin auth is intentionally simple and should be extended with refresh tokens, user management, and stricter production security controls.

## Future Improvements

- Add a real seat detector/classifier and camera calibration per facility
- Add live camera frame sampling with configurable schedules
- Add alert thresholds and notification channels
- Add CSV export for facility analytics
- Add object storage support for S3/GCS
- Add Playwright end-to-end tests for upload and admin workflows
- Add role-based access beyond the seeded admin
- Add model confidence summaries and detector health telemetry

## Resume-Style Highlights

- Designed a full-stack, database-backed facility analytics platform with FastAPI, Next.js, PostgreSQL, SQLAlchemy, Alembic, and Docker Compose
- Implemented modular CV inference architecture with a YOLO-ready detector interface and graceful mock fallback
- Built historical occupancy tracking, congestion scoring, peak-hour analytics, and busiest-facility ranking queries
- Created JWT-protected admin workflows for facility management and operational monitoring
- Added migration, seed, and test coverage to support reproducible local demos and continued development

