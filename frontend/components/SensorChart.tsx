"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { shortDate } from "@/lib/format";
import type { SensorLog } from "@/types/api";

export function SensorChart({ data }: { data: SensorLog[] }) {
  const chartData = [...data]
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map((point) => ({
      label: shortDate(point.timestamp),
      power_kw: Number(point.power_kw.toFixed(2)),
      temperature: Number(point.temperature.toFixed(1)),
      humidity: Number(point.humidity.toFixed(1)),
      noise_level: Number(point.noise_level.toFixed(1)),
      door_count: point.door_count
    }));

  if (!chartData.length) {
    return (
      <div className="grid h-80 place-items-center rounded-lg border border-dashed border-line bg-white text-sm text-slate-500">
        No sensor telemetry yet
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-ink">Sensor and Energy Trend</h2>
        <p className="mt-1 text-sm text-slate-500">
          Synthetic facility telemetry for temperature, power draw, and door activity.
        </p>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#DDE5ED" strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fill: "#64748B", fontSize: 12 }} minTickGap={24} />
            <YAxis tick={{ fill: "#64748B", fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="power_kw" stroke="#1F8A70" strokeWidth={2} dot={false} name="Power (kW)" />
            <Line type="monotone" dataKey="temperature" stroke="#0F766E" strokeWidth={2} dot={false} name="Temp (C)" />
            <Line type="monotone" dataKey="door_count" stroke="#F59E0B" strokeWidth={2} dot={false} name="Door count" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
