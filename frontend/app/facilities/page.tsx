import { FacilityCard } from "@/components/FacilityCard";
import { api } from "@/lib/api";

export default async function FacilitiesPage() {
  const facilities = await api.facilities().catch(() => []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-ink">Facilities</h1>
        <p className="mt-2 text-slate-600">Browse current occupancy estimates and open detailed analytics for each space.</p>
      </div>
      {facilities.length ? (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {facilities.map((status) => <FacilityCard key={status.facility.id} status={status} />)}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-line bg-white p-10 text-center text-slate-500">No facilities are available yet.</div>
      )}
    </div>
  );
}

