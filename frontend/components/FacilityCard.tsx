import Image from "next/image";
import Link from "next/link";

import { CongestionBadge } from "@/components/Badge";
import { percent, shortDate } from "@/lib/format";
import type { FacilityStatus } from "@/types/api";

export function FacilityCard({ status }: { status: FacilityStatus }) {
  const image = status.facility.image_url ?? "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=1200&q=80";

  return (
    <Link href={`/facilities/${status.facility.id}`} className="group overflow-hidden rounded-lg border border-line bg-white shadow-soft transition hover:-translate-y-0.5 hover:shadow-lg">
      <div className="relative h-44 w-full bg-slate-200">
        <Image
          src={image}
          alt={status.facility.name}
          fill
          unoptimized
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 33vw"
        />
      </div>
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-lg font-semibold text-ink group-hover:text-mint">{status.facility.name}</p>
            <p className="mt-1 text-sm text-slate-500">{status.facility.location}</p>
          </div>
          <CongestionBadge level={status.congestion_level} />
        </div>
        <div className="mt-5 grid grid-cols-3 gap-3 text-center">
          <div className="rounded-lg bg-panel p-3">
            <p className="text-xs text-slate-500">People</p>
            <p className="text-lg font-semibold">{status.people_count}</p>
          </div>
          <div className="rounded-lg bg-panel p-3">
            <p className="text-xs text-slate-500">Open</p>
            <p className="text-lg font-semibold">{status.available_seats}</p>
          </div>
          <div className="rounded-lg bg-panel p-3">
            <p className="text-xs text-slate-500">Rate</p>
            <p className="text-lg font-semibold">{percent(status.occupancy_rate)}</p>
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-500">Updated {shortDate(status.latest_analysis_at)}</p>
      </div>
    </Link>
  );
}

