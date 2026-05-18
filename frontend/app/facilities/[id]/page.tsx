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

  const [facility, status, latestStatus, history, summary, sensorLogs, sensorSummary, forecast, recommendations] = await Promise.all([
    api.facility(id).catch(() => null),
    api.status(id).catch(() => null),
    api.latestStatus(id).catch(() => null),
    api.history(id).catch(() => []),
    api.facilitySummary(id).catch(() => null),
    api.sensorLogs(id).catch(() => []),
    api.sensorSummary(id).catch(() => null),
    api.forecast(id).catch(() => null),
    api.recommendations(id).catch(() => [])
  ]);

  if (!facility || !status || !latestStatus || !summary || !forecast) notFound();

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
        <ForecastCard forecast={forecast} />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
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
              {history.slice(0, 12).map((point) => (
                <tr key={point.timestamp}>
                  <td className="py-3">{shortDate(point.timestamp)}</td>
                  <td>{point.people_count}</td>
                  <td>{point.occupied_seats}</td>
                  <td>{point.available_seats}</td>
                  <td>{percent(point.occupancy_rate)}</td>
                  <td><CongestionBadge level={point.congestion_level} /></td>
                  <td>{point.congestion_level === "High" ? "High congestion event" : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
