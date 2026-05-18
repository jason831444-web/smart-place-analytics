import clsx from "clsx";

import { shortDate } from "@/lib/format";
import type { Recommendation } from "@/types/api";

const severityStyles: Record<Recommendation["severity"], string> = {
  low: "border-emerald-200 bg-emerald-50 text-emerald-900",
  medium: "border-amber-200 bg-amber-50 text-amber-900",
  high: "border-rose-200 bg-rose-50 text-rose-900"
};

export function RecommendationList({ items }: { items: Recommendation[] }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-ink">Operational Recommendations</h2>
        <p className="mt-1 text-sm text-slate-500">
          Actionable suggestions generated from current occupancy, forecast, and sensor context.
        </p>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={`${item.recommendation_type}-${index}`} className={clsx("rounded-lg border p-4", severityStyles[item.severity])}>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em]">{item.severity}</p>
                <h3 className="mt-1 text-base font-semibold">{item.title}</h3>
              </div>
              <p className="text-xs">{shortDate(item.created_at)}</p>
            </div>
            <p className="mt-3 text-sm leading-6">{item.message}</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
              {item.evidence.map((entry) => (
                <li key={entry}>{entry}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
