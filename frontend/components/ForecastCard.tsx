import { CongestionBadge } from "@/components/Badge";
import { percent, shortDate } from "@/lib/format";
import type { Forecast } from "@/types/api";

export function ForecastCard({ forecast }: { forecast: Forecast }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Near-Term Forecast</h2>
          <p className="mt-1 text-sm text-slate-500">
            Predicted occupancy for the next {forecast.window_minutes} minutes.
          </p>
        </div>
        <CongestionBadge level={forecast.predicted_congestion_level} />
      </div>
      <p className="mt-5 text-4xl font-semibold text-ink">{percent(forecast.predicted_occupancy_rate)}</p>
      <div className="mt-4 grid gap-2 text-sm text-slate-600">
        <p>Confidence: {Math.round(forecast.confidence * 100)}%</p>
        <p>Method: {forecast.method}</p>
        <p>Generated: {shortDate(forecast.generated_at)}</p>
      </div>
      <p className="mt-4 rounded-lg bg-panel p-3 text-sm leading-6 text-slate-600">{forecast.explanation}</p>
    </div>
  );
}
