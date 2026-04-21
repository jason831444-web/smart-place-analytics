"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Facility } from "@/types/api";

type Draft = {
  name: string;
  type: string;
  location: string;
  description: string;
  total_seats: number;
  image_url: string;
};

const emptyDraft: Draft = {
  name: "",
  type: "Library",
  location: "",
  description: "",
  total_seats: 0,
  image_url: ""
};

export function FacilityManager() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setFacilities(await api.adminFacilities());
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : "Unable to load facilities"));
  }, []);

  function edit(facility: Facility) {
    setEditingId(facility.id);
    setDraft({
      name: facility.name,
      type: facility.type,
      location: facility.location,
      description: facility.description ?? "",
      total_seats: facility.total_seats,
      image_url: facility.image_url ?? ""
    });
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const payload = { ...draft, description: draft.description || null, image_url: draft.image_url || null };
    if (editingId) await api.updateFacility(editingId, payload);
    else await api.createFacility(payload);
    setDraft(emptyDraft);
    setEditingId(null);
    await load();
  }

  async function remove(id: number) {
    await api.deleteFacility(id);
    await load();
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
      <form onSubmit={submit} className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h1 className="text-2xl font-semibold text-ink">{editingId ? "Edit Facility" : "Create Facility"}</h1>
        <div className="mt-5 grid gap-4">
          {(["name", "type", "location", "image_url"] as const).map((field) => (
            <label key={field} className="block text-sm font-medium text-slate-700">
              {field.replace("_", " ")}
              <input
                className="focus-ring mt-2 w-full rounded-lg border border-line px-3 py-2"
                value={draft[field]}
                onChange={(event) => setDraft((current) => ({ ...current, [field]: event.target.value }))}
              />
            </label>
          ))}
          <label className="block text-sm font-medium text-slate-700">
            total seats
            <input
              className="focus-ring mt-2 w-full rounded-lg border border-line px-3 py-2"
              type="number"
              min={0}
              value={draft.total_seats}
              onChange={(event) => setDraft((current) => ({ ...current, total_seats: Number(event.target.value) }))}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            description
            <textarea
              className="focus-ring mt-2 min-h-28 w-full rounded-lg border border-line px-3 py-2"
              value={draft.description}
              onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
            />
          </label>
        </div>
        <div className="mt-5 flex gap-3">
          <button className="focus-ring rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white">{editingId ? "Save changes" : "Create"}</button>
          {editingId ? <button type="button" onClick={() => { setEditingId(null); setDraft(emptyDraft); }} className="focus-ring rounded-lg border border-line px-4 py-2 text-sm font-semibold">Cancel</button> : null}
        </div>
        {error ? <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      </form>

      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <h2 className="text-xl font-semibold text-ink">Facilities</h2>
        <div className="mt-4 space-y-3">
          {facilities.map((facility) => (
            <div key={facility.id} className="flex flex-col gap-3 rounded-lg bg-panel p-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-semibold text-ink">{facility.name}</p>
                <p className="text-sm text-slate-500">{facility.type} · {facility.location} · {facility.total_seats} seats</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => edit(facility)} className="focus-ring rounded-lg border border-line bg-white px-3 py-2 text-sm font-semibold">Edit</button>
                <button onClick={() => remove(facility.id)} className="focus-ring rounded-lg bg-rose-600 px-3 py-2 text-sm font-semibold text-white">Delete</button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

