"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { toTrendSeries } from "@/lib/historyChart";
import type { HistoryPoint } from "@/types/api";

export function HistoryChart({ data }: { data: HistoryPoint[] }) {
  const series = toTrendSeries(data);
  const chartData = series.points.map((point) => ({
    label: point.label,
    occupancy_percent: point.occupancy_percent,
    average_people_count: point.average_people_count,
    samples: point.samples
  }));

  if (!chartData.length) {
    return (
      <div className="grid h-80 place-items-center rounded-lg border border-dashed border-line bg-white text-sm text-slate-500">
        No historical analyses yet
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">Occupancy History</h2>
          <p className="mt-1 text-sm text-slate-500">
            {series.grain === "daily"
              ? "Daily average occupancy"
              : series.grain === "hourly"
                ? "Hourly average occupancy"
                : "5-minute average occupancy"}
          </p>
        </div>
        <p className="text-xs text-slate-500">{data.length} saved occupancy samples</p>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 8, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="occupancyFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#1F8A70" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#1F8A70" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#DDE5ED" strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fill: "#64748B", fontSize: 12 }} minTickGap={24} />
            <YAxis tick={{ fill: "#64748B", fontSize: 12 }} domain={[0, 100]} unit="%" />
            <Tooltip
              formatter={(value: number, name: string) => [
                name === "occupancy_percent" ? `${value}%` : value,
                name === "occupancy_percent" ? "Avg occupancy" : "Avg people"
              ]}
            />
            <Area
              type="monotone"
              dataKey="occupancy_percent"
              stroke="#1F8A70"
              fill="url(#occupancyFill)"
              strokeWidth={3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
