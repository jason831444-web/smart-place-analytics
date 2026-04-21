"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { HistoryPoint } from "@/types/api";

export function HistoryChart({ data }: { data: HistoryPoint[] }) {
  const chartData = [...data]
    .reverse()
    .map((point) => ({ ...point, time: new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric" }).format(new Date(point.timestamp)) }));

  if (!chartData.length) {
    return <div className="grid h-72 place-items-center rounded-lg border border-dashed border-line bg-white text-sm text-slate-500">No historical analyses yet</div>;
  }

  return (
    <div className="h-72 rounded-lg border border-line bg-white p-4 shadow-soft">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#DDE5ED" />
          <XAxis dataKey="time" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value) => `${Math.round(Number(value) * 100)}%`} />
          <Area type="monotone" dataKey="occupancy_rate" stroke="#1F8A70" fill="#BDE7DB" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

