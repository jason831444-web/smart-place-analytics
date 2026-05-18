# API Reference

This file is a concise route map for Smart Place Analytics. For request/response behavior, use the OpenAPI docs at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend is running.

## Facilities

- `GET /api/facilities`
- `GET /api/facilities/{facility_id}`
- `GET /api/facilities/{facility_id}/status`
- `GET /api/facilities/{facility_id}/history`
- `GET /api/facilities/{facility_id}/occupancy-logs`
- `GET /api/facilities/{facility_id}/latest-status`
- `GET /api/facilities/{facility_id}/summary`

## Sensor logs and telemetry

- `GET /api/facilities/{facility_id}/sensor-logs`
- `GET /api/facilities/{facility_id}/sensor-summary`
- `GET /api/facilities/{facility_id}/operations-alerts`

MQTT verification endpoints:

- `GET /api/facilities/{facility_id}/sensor-logs`
- `GET /api/operations/job-status`

## Rollups

- `GET /api/facilities/{facility_id}/rollups`
- `GET /api/facilities/{facility_id}/rollups/latest`
- `POST /api/facilities/{facility_id}/rollups/compute`

## Uploads and live analysis

- `POST /api/uploads`
- `POST /api/uploads/analyze`
- `GET /api/analyses/{analysis_id}`
- `POST /api/live/analyze`

## Forecast and recommendations

- `GET /api/facilities/{facility_id}/forecast?window_minutes=60`
- `GET /api/facilities/{facility_id}/recommendations`

## Operations observability

- `GET /api/operations/job-status`
- `GET /api/operations/job-runs`
- `GET /api/operations/alerts`

## Admin

- `POST /api/auth/login`
- `GET /api/admin/facilities`
- `POST /api/admin/facilities`
- `PUT /api/admin/facilities/{facility_id}`
- `DELETE /api/admin/facilities/{facility_id}`
- `GET /api/admin/analytics/overview`
- `GET /api/admin/analytics/facilities/{facility_id}`

## Practical verification flow

1. Upload or analyze a live frame
2. Check facility history and occupancy logs
3. Run background jobs or MQTT publisher/subscriber
4. Check sensor logs and rollups
5. Check operations status, job runs, and active alerts
