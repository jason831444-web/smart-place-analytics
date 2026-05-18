export default function FacilityLiveLoading() {
  return (
    <div className="space-y-6">
      <div className="h-40 animate-pulse rounded-lg border border-line bg-white" />
      <div className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="aspect-video animate-pulse rounded-lg border border-line bg-slate-200" />
        <div className="min-h-80 animate-pulse rounded-lg border border-line bg-white" />
      </div>
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="h-72 animate-pulse rounded-lg border border-line bg-white" />
        <div className="h-72 animate-pulse rounded-lg border border-line bg-white" />
      </div>
    </div>
  );
}
