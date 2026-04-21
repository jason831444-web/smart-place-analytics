"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { CongestionBadge } from "@/components/Badge";
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import { percent, score, shortDate } from "@/lib/format";
import type { AnalyticsOverview } from "@/types/api";

export function AdminDashboard() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.adminOverview().then(setData).catch((err) => setError(err instanceof Error ? err.message : "Unable to load dashboard"));
  }, []);

  if (error) {
    return <div className="rounded-lg border border-rose-200 bg-rose-50 p-5 text-rose-700">Admin access required. Sign in and return to this page.</div>;
  }

  if (!data) {
    return <div className="rounded-lg border border-line bg-white p-10 text-center text-slate-500">Loading dashboard...</div>;
  }

  const hourData = data.peak_hours.map((item) => ({ hour: `${item.hour}:00`, occupancy: item.average_occupancy_rate }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">Admin Dashboard</h1>
          <p className="mt-2 text-slate-600">Operational summary, busiest spaces, peak hours, and recent activity.</p>
        </div>
        <a className="focus-ring rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white" href="/admin/facilities">Manage facilities</a>
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
          <h2 className="text-lg font-semibold text-ink">Peak Hours</h2>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#DDE5ED" />
                <XAxis dataKey="hour" />
                <YAxis tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} />
                <Tooltip formatter={(value) => `${Math.round(Number(value) * 100)}%`} />
                <Bar dataKey="occupancy" fill="#1F8A70" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">Busiest Facilities</h2>
          <div className="mt-4 space-y-3">
            {data.busiest_facilities.map((facility) => (
              <div key={facility.facility_id} className="flex items-center justify-between gap-4 rounded-lg bg-panel p-3">
                <div>
                  <p className="font-medium text-ink">{facility.facility_name}</p>
                  <p className="text-sm text-slate-500">{facility.analyses_count} analyses · {percent(facility.average_occupancy_rate)} avg occupancy</p>
                </div>
                {facility.latest_congestion_level ? <CongestionBadge level={facility.latest_congestion_level} /> : null}
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
              <tr><th className="py-3">Time</th><th>Facility</th><th>People</th><th>Occupancy</th><th>Level</th></tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.recent_activity.map((item) => (
                <tr key={item.analysis_id}>
                  <td className="py-3">{shortDate(item.created_at)}</td>
                  <td>{item.facility_name}</td>
                  <td>{item.people_count}</td>
                  <td>{percent(item.occupancy_rate)}</td>
                  <td><CongestionBadge level={item.congestion_level} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

