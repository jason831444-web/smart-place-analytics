export default function FacilityDetailLoading() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
        <div className="min-h-80 animate-pulse rounded-lg border border-line bg-slate-200" />
        <div className="min-h-80 animate-pulse rounded-lg border border-line bg-white" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-32 animate-pulse rounded-lg border border-line bg-white" />
        ))}
      </div>
      <div className="h-80 animate-pulse rounded-lg border border-line bg-white" />
      <div className="h-80 animate-pulse rounded-lg border border-line bg-white" />
    </div>
  );
}
