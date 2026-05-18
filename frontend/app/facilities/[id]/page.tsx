import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CongestionBadge } from "@/components/Badge";
import { ForecastCard } from "@/components/ForecastCard";
import { HistoryChart } from "@/components/HistoryChart";
import { MetricCard } from "@/components/MetricCard";
import { RecommendationList } from "@/components/RecommendationList";
import { SensorChart } from "@/components/SensorChart";
import { UploadAnalyzer } from "@/components/UploadAnalyzer";
import { api } from "@/lib/api";
import { percent, score, shortDate } from "@/lib/format";
import type { FacilityOperationalRollup, FacilityStatus, FacilitySummary, Forecast, JobStatus, LatestStatus, OperationalAlert } from "@/types/api";

function operationsHealth(jobStatus: JobStatus | null, alerts: OperationalAlert[]): { label: "healthy" | "warning" | "stale"; tone: string } {
  const hasStaleness = alerts.some((alert) => alert.alert_type === "stale_telemetry" || alert.alert_type === "overdue_rollup");
  const latestJobStatus = jobStatus?.latest_job_run?.status;

  if (!jobStatus?.latest_job_run || latestJobStatus === "failed" || hasStaleness) {
    return { label: "stale", tone: "bg-rose-50 text-rose-700 border-rose-200" };
  }
  if (latestJobStatus === "partial" || alerts.length > 0) {
    return { label: "warning", tone: "bg-amber-50 text-amber-700 border-amber-200" };
  }
  return { label: "healthy", tone: "bg-emerald-50 text-emerald-700 border-emerald-200" };
}

export default async function FacilityDetailPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: idParam } = await params;
  const id = Number(idParam);

  if (!Number.isFinite(id)) {
    notFound();
  }

  const [facility, statusResponse, latestStatusResponse, history, summaryResponse, sensorLogs, sensorSummary, latestRollupResponse, jobStatusResponse, facilityAlerts, forecastResponse, recommendations] = await Promise.all([
    api.facility(id).catch(() => null),
    api.status(id).catch(() => null),
    api.latestStatus(id).catch(() => null),
    api.history(id).catch(() => []),
    api.facilitySummary(id).catch(() => null),
    api.sensorLogs(id).catch(() => []),
    api.sensorSummary(id).catch(() => null),
    api.latestRollup(id).catch(() => null),
    api.jobStatus().catch(() => null),
    api.facilityOperationsAlerts(id).catch(() => []),
    api.forecast(id).catch(() => null),
    api.recommendations(id).catch(() => [])
  ]);

  if (!facility) notFound();

  const status: FacilityStatus =
    statusResponse ??
    {
      facility,
      people_count: 0,
      occupied_seats: 0,
      available_seats: facility.total_seats,
      occupancy_rate: 0,
      congestion_level: "Low",
      congestion_score: 0,
      latest_analysis_id: null,
      latest_analysis_at: null
    };

  const latestStatus: LatestStatus =
    latestStatusResponse ??
    {
      facility_id: facility.id,
      timestamp: status.latest_analysis_at ?? null,
      people_count: status.people_count,
      occupied_seats: status.occupied_seats,
      available_seats: status.available_seats,
      occupancy_rate: status.occupancy_rate,
      congestion_score: status.congestion_score,
      congestion_level: status.congestion_level,
      confidence: null,
      source_type: null,
      analysis_id: status.latest_analysis_id ?? null,
      image_url: null,
      annotated_image_url: null
    };

  const summary: FacilitySummary =
    summaryResponse ??
    {
      facility_id: facility.id,
      latest_occupancy_rate: status.occupancy_rate,
      average_occupancy_rate: 0,
      peak_occupancy_rate: 0,
      high_congestion_events: 0,
      most_recent_timestamp: latestStatus.timestamp ?? null,
      latest_people_count: latestStatus.people_count,
      samples: history.length
    };

  const forecast: Forecast | null = forecastResponse;
  const latestRollup: FacilityOperationalRollup | null = latestRollupResponse;
  const jobStatus: JobStatus | null = jobStatusResponse;
  const pipelineHealth = operationsHealth(jobStatus, facilityAlerts);

  const image =
    facility.image_url ??
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1400&q=80";

  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
        <div className="relative min-h-80 overflow-hidden rounded-lg border border-line bg-slate-200 shadow-soft">
          <Image
            src={image}
            alt={facility.name}
            fill
            unoptimized
            className="object-cover"
            priority
          />
        </div>
        <div className="rounded-lg border border-line bg-white p-6 shadow-soft">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-mint">{facility.type}</p>
              <h1 className="mt-3 text-3xl font-semibold text-ink">{facility.name}</h1>
              <p className="mt-2 text-slate-500">{facility.location}</p>
            </div>
            <CongestionBadge level={status.congestion_level} />
          </div>
          <p className="mt-5 text-sm leading-6 text-slate-600">{facility.description}</p>
          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-slate-500">Latest analysis {shortDate(status.latest_analysis_at)}</p>
            <Link href={`/facilities/${facility.id}/live`} className="focus-ring rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white">
              Open live monitor
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="People detected" value={status.people_count} />
        <MetricCard label="Occupied seats" value={status.occupied_seats} />
        <MetricCard label="Available seats" value={status.available_seats} hint={`${facility.total_seats} total seats`} />
        <MetricCard label="Occupancy rate" value={percent(status.occupancy_rate)} />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Latest occupancy" value={percent(summary.latest_occupancy_rate)} hint={`Updated ${shortDate(summary.most_recent_timestamp)}`} />
        <MetricCard label="Average occupancy" value={percent(summary.average_occupancy_rate)} hint={`${summary.samples} occupancy samples`} />
        <MetricCard label="Peak occupancy" value={percent(summary.peak_occupancy_rate)} hint="Highest recorded occupancy rate" />
        <MetricCard label="High congestion events" value={summary.high_congestion_events} hint="Events recorded at high congestion" />
      </section>

      <UploadAnalyzer facilityId={facility.id} />

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <HistoryChart data={history} />
        {forecast ? (
          <ForecastCard forecast={forecast} />
        ) : (
          <div className="rounded-lg border border-line bg-white p-5 shadow-soft text-sm text-slate-500">
            Forecast data is temporarily unavailable.
          </div>
        )}
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-ink">Live Status</h2>
              <p className="mt-1 text-sm text-slate-500">
                Last system update {shortDate(latestStatus.timestamp)}
              </p>
            </div>
            <CongestionBadge level={latestStatus.congestion_level} />
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <MetricCard label="Current occupancy" value={percent(latestStatus.occupancy_rate)} hint={`Score ${score(latestStatus.congestion_score)}`} />
            <MetricCard label="Source" value={latestStatus.source_type ?? "unknown"} hint={`Confidence ${latestStatus.confidence ? `${Math.round(latestStatus.confidence * 100)}%` : "n/a"}`} />
            <MetricCard label="People count" value={latestStatus.people_count} />
            <MetricCard label="Available seats" value={latestStatus.available_seats} />
          </div>
        </div>

        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">System Status</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <p>Latest occupancy sample: {shortDate(summary.most_recent_timestamp)}</p>
            <p>Sensor stream status: {sensorSummary?.samples ? `Active · ${sensorSummary.samples} samples` : "No sensor telemetry yet"}</p>
            <p>Live monitoring route: <Link href={`/facilities/${facility.id}/live`} className="font-semibold text-mint">/facilities/{facility.id}/live</Link></p>
            <p>Current congestion level: {latestStatus.congestion_level}</p>
          </div>
        </div>

        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <h2 className="text-lg font-semibold text-ink">Operations Pipeline</h2>
            <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${pipelineHealth.tone}`}>
              {pipelineHealth.label}
            </span>
          </div>
          <div className="mt-4 space-y-3 text-sm text-slate-600">
            <p>
              Latest job run: {jobStatus?.latest_job_run ? `${jobStatus.latest_job_run.status} · ${shortDate(jobStatus.latest_job_run.finished_at ?? jobStatus.latest_job_run.started_at)}` : "No job run recorded yet"}
            </p>
            <p>Latest sensor update: {shortDate(jobStatus?.latest_sensor_log_at ?? null)}</p>
            <p>Latest rollup: {shortDate(latestRollup?.timestamp ?? jobStatus?.latest_rollup_at ?? null)}</p>
            <p>
              Rollup window: {latestRollup ? `${latestRollup.window_minutes} minutes` : "No rollup computed yet"}
            </p>
            <p>
              Recent activity: {jobStatus ? `${jobStatus.facilities_with_recent_activity} facilities · ${jobStatus.total_rollups} rollups stored` : "Job status unavailable"}
            </p>
            <p>Active alerts: {jobStatus?.active_alert_count ?? facilityAlerts.length}</p>
            <p>
              Local runner: <code className="rounded bg-panel px-1.5 py-0.5 text-xs text-ink">python scripts/run_operations_jobs.py --interval-seconds 30</code>
            </p>
          </div>
          <div className="mt-4 space-y-2 border-t border-line pt-4 text-sm text-slate-600">
            {facilityAlerts.length ? (
              facilityAlerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="rounded-lg bg-panel p-3">
                  <p className="font-semibold text-ink">{alert.title}</p>
                  <p className="mt-1 leading-6">{alert.message}</p>
                </div>
              ))
            ) : (
              <p>No active operational alerts for this facility.</p>
            )}
          </div>
        </div>
      </section>

      <SensorChart data={sensorLogs} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Temperature" value={sensorSummary?.latest_temperature != null ? `${sensorSummary.latest_temperature.toFixed(1)} C` : "n/a"} />
        <MetricCard label="Humidity" value={sensorSummary?.latest_humidity != null ? `${sensorSummary.latest_humidity.toFixed(0)}%` : "n/a"} />
        <MetricCard label="Power draw" value={sensorSummary?.latest_power_kw != null ? `${sensorSummary.latest_power_kw.toFixed(1)} kW` : "n/a"} />
        <MetricCard label="Door count" value={sensorSummary?.latest_door_count ?? "n/a"} />
        <MetricCard label="Noise level" value={sensorSummary?.latest_noise_level != null ? `${sensorSummary.latest_noise_level.toFixed(0)} dB` : "n/a"} />
      </section>

      <RecommendationList items={recommendations} />

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold text-ink">Recent Occupancy Events</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3">Time</th>
                <th>People</th>
                <th>Occupied</th>
                <th>Available</th>
                <th>Rate</th>
                <th>Level</th>
                <th>Alert</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {history.length ? (
                history.slice(0, 12).map((point) => (
                  <tr key={point.timestamp}>
                    <td className="py-3">{shortDate(point.timestamp)}</td>
                    <td>{point.people_count}</td>
                    <td>{point.occupied_seats}</td>
                    <td>{point.available_seats}</td>
                    <td>{percent(point.occupancy_rate)}</td>
                    <td><CongestionBadge level={point.congestion_level} /></td>
                    <td>{point.congestion_level === "High" ? "High congestion event" : "-"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="py-6 text-slate-500" colSpan={7}>No occupancy events have been recorded yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
