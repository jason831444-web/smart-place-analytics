import clsx from "clsx";

import type { CongestionLevel } from "@/types/api";

const styles: Record<CongestionLevel, string> = {
  Low: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Medium: "bg-amber-100 text-amber-900 border-amber-200",
  High: "bg-rose-100 text-rose-800 border-rose-200"
};

export function CongestionBadge({ level }: { level: CongestionLevel }) {
  return <span className={clsx("rounded-full border px-3 py-1 text-xs font-semibold", styles[level])}>{level}</span>;
}

