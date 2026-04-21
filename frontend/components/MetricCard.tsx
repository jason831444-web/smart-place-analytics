import type { ReactNode } from "react";

export function MetricCard({ label, value, hint, icon }: { label: string; value: string | number; hint?: string; icon?: ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {icon ? <div className="text-mint">{icon}</div> : null}
      </div>
      <p className="mt-3 text-3xl font-semibold text-ink">{value}</p>
      {hint ? <p className="mt-2 text-sm text-slate-500">{hint}</p> : null}
    </div>
  );
}

