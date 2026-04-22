"use client";

import { toTrendSeries, type TrendPoint } from "@/lib/historyChart";
import type { HistoryPoint } from "@/types/api";

function tooltipLabel(point: TrendPoint): string {
  const suffix = point.samples === 1 ? "1 analysis" : `${point.samples} analyses`;
  return `${point.label} · ${suffix}`;
}

export function HistoryChart({ data }: { data: HistoryPoint[] }) {
  const series = toTrendSeries(data);

  const chartData = series.points
    .map((point) => ({
      ...point,
      label: String(point.label ?? ""),
      occupancy_percent: Number(point.occupancy_percent),
      average_people_count: Number(point.average_people_count),
      samples: Number(point.samples ?? 0)
    }))
    .filter(
      (point) =>
        point.label.length > 0 &&
        Number.isFinite(point.occupancy_percent) &&
        Number.isFinite(point.average_people_count) &&
        Number.isFinite(point.samples)
    );

  if (!chartData.length) {
    return (
      <div className="grid h-72 place-items-center rounded-lg border border-dashed border-line bg-white text-sm text-slate-500">
        No historical analyses yet
      </div>
    );
  }

  const width = Math.max(760, chartData.length * 120);
  const height = 320;
  const paddingLeft = 56;
  const paddingRight = 24;
  const paddingTop = 24;
  const paddingBottom = 48;

  const plotWidth = width - paddingLeft - paddingRight;
  const plotHeight = height - paddingTop - paddingBottom;

  const maxY = 100;
  const minY = 0;

  const xStep = chartData.length > 1 ? plotWidth / (chartData.length - 1) : 0;

  const points = chartData.map((point, index) => {
    const x = paddingLeft + index * xStep;
    const y =
      paddingTop +
      ((maxY - point.occupancy_percent) / (maxY - minY)) * plotHeight;

    return {
      ...point,
      x,
      y
    };
  });

  const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(" ");

  const areaPoints = [
    `${paddingLeft},${paddingTop + plotHeight}`,
    ...points.map((point) => `${point.x},${point.y}`),
    `${paddingLeft + plotWidth},${paddingTop + plotHeight}`
  ].join(" ");

  const yTicks = [0, 20, 40, 60, 80, 100];

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">
            {series.grain === "daily"
              ? "Daily average occupancy"
              : series.grain === "hourly"
                ? "Hourly average occupancy"
                : "5-minute average occupancy"}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            X-axis: date · Y-axis: average occupancy percentage
          </p>
        </div>
        <div className="text-xs text-slate-500">{data.length} saved analyses</div>
      </div>

      <div className="mb-4 rounded-lg bg-panel px-3 py-2 text-xs text-slate-600">
        {chartData.map((point) => `${point.label}: ${point.occupancy_percent}%`).join(" | ")}
      </div>

      <div className="overflow-x-auto">
        <svg width={width} height={height} className="block">
          {yTicks.map((tick) => {
            const y =
              paddingTop + ((maxY - tick) / (maxY - minY)) * plotHeight;

            return (
              <g key={tick}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={paddingLeft + plotWidth}
                  y2={y}
                  stroke="#DDE5ED"
                  strokeDasharray="3 3"
                />
                <text
                  x={paddingLeft - 10}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="12"
                  fill="#64748B"
                >
                  {tick}%
                </text>
              </g>
            );
          })}

          <polygon points={areaPoints} fill="#BDE7DB" fillOpacity="0.5" />

          <polyline
            points={polylinePoints}
            fill="none"
            stroke="#1F8A70"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {points.map((point) => (
            <g key={point.label}>
              <circle cx={point.x} cy={point.y} r="5" fill="#1F8A70" stroke="#ffffff" strokeWidth="2" />
              <text
                x={point.x}
                y={point.y - 12}
                textAnchor="middle"
                fontSize="12"
                fontWeight="500"
                fill="#475569"
              >
                {point.occupancy_percent}%
              </text>
              <text
                x={point.x}
                y={paddingTop + plotHeight + 24}
                textAnchor="middle"
                fontSize="12"
                fill="#64748B"
              >
                {point.label}
              </text>
              <title>{tooltipLabel(point)} · Avg occupancy: {point.occupancy_percent}%</title>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}