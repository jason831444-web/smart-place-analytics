"use client";

import { useEffect, useState } from "react";

import { CongestionBadge } from "@/components/Badge";
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import { percent, score, shortDate } from "@/lib/format";
import type { AnalyticsOverview } from "@/types/api";

export function AdminDashboard() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .adminOverview()
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Unable to load dashboard")
      );
  }, []);

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-5 text-rose-700">
        Admin access required. Sign in and return to this page.
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg border border-line bg-white p-10 text-center text-slate-500">
        Loading dashboard...
      </div>
    );
  }

  const hourData = data.peak_hours.map((item) => ({
    hour: `${String(item.hour).padStart(2, "0")}:00`,
    occupancyPercent: Math.round(item.average_occupancy_rate * 100),
    samples: item.samples
  }));

  const maxPeakValue = Math.max(...hourData.map((item) => item.occupancyPercent), 1);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">Admin Dashboard</h1>
          <p className="mt-2 text-slate-600">
            Operational summary, busiest spaces, peak hours, and recent activity.
          </p>
        </div>
        <a
          className="focus-ring rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white"
          href="/admin/facilities"
        >
          Manage facilities
        </a>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Facilities" value={data.facilities_count} />
        <MetricCard label="Uploads" value={data.uploads_count} />
        <MetricCard label="Analyses" value={data.analyses_count} />
        <MetricCard label="Avg occupancy" value={percent(data.average_occupancy_rate)} />
        <MetricCard label="Avg score" value={score(data.average_congestion_score)} />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-lg font-semibold text-ink">Peak Hours</h2>
            <p className="text-xs text-slate-500">
              Hourly average occupancy over the last 14 days
            </p>
          </div>

          {hourData.length === 0 ? (
            <div className="mt-4 grid h-72 place-items-center rounded-lg border border-dashed border-line bg-panel text-sm text-slate-500">
              No peak-hour data yet
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-[64px_1fr_64px] gap-3 px-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>Hour</span>
                <span>Occupancy</span>
                <span className="text-right">Value</span>
              </div>

              {hourData.map((item) => {
                const widthPercent = Math.max(
                  6,
                  Math.round((item.occupancyPercent / maxPeakValue) * 100)
                );

                return (
                  <div
                    key={item.hour}
                    className="grid grid-cols-[64px_1fr_64px] items-center gap-3 rounded-lg bg-panel px-3 py-3"
                    title={`${item.hour} · ${item.occupancyPercent}% avg occupancy · ${item.samples} samples`}
                  >
                    <div className="text-sm font-medium text-ink">{item.hour}</div>

                    <div>
                      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
                        <div
                          className="h-full rounded-full bg-mint"
                          style={{ width: `${widthPercent}%` }}
                        />
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.samples} sample{item.samples === 1 ? "" : "s"}
                      </p>
                    </div>

                    <div className="text-right text-sm font-semibold text-ink">
                      {item.occupancyPercent}%
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">Busiest Facilities</h2>
          <div className="mt-4 space-y-3">
            {data.busiest_facilities.map((facility) => (
              <div
                key={facility.facility_id}
                className="flex items-center justify-between gap-4 rounded-lg bg-panel p-3"
              >
                <div>
                  <p className="font-medium text-ink">{facility.facility_name}</p>
                  <p className="text-sm text-slate-500">
                    {facility.analyses_count} analyses ·{" "}
                    {percent(facility.average_occupancy_rate)} avg occupancy
                  </p>
                </div>
                {facility.latest_congestion_level ? (
                  <CongestionBadge level={facility.latest_congestion_level} />
                ) : null}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold text-ink">Recent System Activity</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-3">Time</th>
                <th>Facility</th>
                <th>People</th>
                <th>Occupancy</th>
                <th>Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.recent_activity.map((item) => (
                <tr key={item.analysis_id}>
                  <td className="py-3">{shortDate(item.created_at)}</td>
                  <td>{item.facility_name}</td>
                  <td>{item.people_count}</td>
                  <td>{percent(item.occupancy_rate)}</td>
                  <td>
                    <CongestionBadge level={item.congestion_level} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}