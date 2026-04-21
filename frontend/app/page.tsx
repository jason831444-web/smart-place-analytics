import Link from "next/link";
import { BuildingLibraryIcon, ChartBarSquareIcon, UsersIcon } from "@heroicons/react/24/outline";

import { FacilityCard } from "@/components/FacilityCard";
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";
import { percent, score } from "@/lib/format";

export default async function HomePage() {
  const facilities = await api.facilities().catch(() => []);
  const avgOccupancy = facilities.length ? facilities.reduce((sum, item) => sum + item.occupancy_rate, 0) / facilities.length : 0;
  const avgScore = facilities.length ? facilities.reduce((sum, item) => sum + item.congestion_score, 0) / facilities.length : 0;

  return (
    <div className="space-y-8">
      <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr] lg:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-mint">Operational analytics</p>
          <h1 className="mt-4 max-w-4xl text-4xl font-semibold tracking-tight text-ink sm:text-6xl">Smart Seat and Facility Congestion Analysis System</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Monitor seats, people count, and congestion across shared facilities with image-based analysis, persistent history, and admin analytics.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/facilities" className="focus-ring rounded-lg bg-ink px-5 py-3 text-sm font-semibold text-white">View facilities</Link>
            <Link href="/admin" className="focus-ring rounded-lg border border-line bg-white px-5 py-3 text-sm font-semibold text-ink">Admin dashboard</Link>
          </div>
        </div>
        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="grid gap-4">
            <MetricCard label="Tracked facilities" value={facilities.length} icon={<BuildingLibraryIcon className="h-6 w-6" />} />
            <MetricCard label="Average occupancy" value={percent(avgOccupancy)} icon={<UsersIcon className="h-6 w-6" />} />
            <MetricCard label="Congestion score" value={score(avgScore)} icon={<ChartBarSquareIcon className="h-6 w-6" />} />
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-ink">Featured Facilities</h2>
            <p className="mt-1 text-sm text-slate-500">Current status from the latest persisted analysis.</p>
          </div>
          <Link href="/facilities" className="text-sm font-semibold text-mint">Open all</Link>
        </div>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {facilities.slice(0, 3).map((status) => <FacilityCard key={status.facility.id} status={status} />)}
        </div>
      </section>
    </div>
  );
}

