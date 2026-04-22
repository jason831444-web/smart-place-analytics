import { notFound } from "next/navigation";

import { LiveMonitor } from "@/components/LiveMonitor";
import { api } from "@/lib/api";

export default async function FacilityLivePage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: idParam } = await params;
  const id = Number(idParam);

  if (!Number.isFinite(id)) {
    notFound();
  }

  const facility = await api.facility(id).catch(() => null);
  if (!facility) notFound();

  return <LiveMonitor facility={facility} />;
}
