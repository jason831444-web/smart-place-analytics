import Image from "next/image";
import { notFound } from "next/navigation";

import { CongestionBadge } from "@/components/Badge";
import { HistoryChart } from "@/components/HistoryChart";
import { MetricCard } from "@/components/MetricCard";
import { UploadAnalyzer } from "@/components/UploadAnalyzer";
import { api } from "@/lib/api";
import { percent, shortDate } from "@/lib/format";

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

  const [facility, status, history] = await Promise.all([
    api.facility(id).catch(() => null),
    api.status(id).catch(() => null),
    api.history(id).catch(() => [])
  ]);

  if (!facility || !status) notFound();

  const image =
    facility.image_url ??
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1400&q=80";

  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
        <div className="relative min-h-80 overflow-hidden rounded-lg border border-line bg-slate-200 shadow-soft">
          <Image src={image} alt={facility.name} fill className="object-cover" priority />
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
          <p className="mt-5 text-xs text-slate-500">Latest analysis {shortDate(status.latest_analysis_at)}</p>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="People detected" value={status.people_count} />
        <MetricCard label="Occupied seats" value={status.occupied_seats} />
        <MetricCard label="Available seats" value={status.available_seats} hint={`${facility.total_seats} total seats`} />
        <MetricCard label="Occupancy rate" value={percent(status.occupancy_rate)} />
      </section>

      <UploadAnalyzer facilityId={facility.id} />

      <section>
        <h2 className="mb-4 text-xl font-semibold text-ink">Occupancy Trend</h2>
        <HistoryChart data={history} />
      </section>

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold text-ink">Recent Analysis History</h2>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}