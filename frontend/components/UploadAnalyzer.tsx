"use client";

import Image from "next/image";
import { useState } from "react";

import { CongestionBadge } from "@/components/Badge";
import { api } from "@/lib/api";
import { percent } from "@/lib/format";
import type { Analysis } from "@/types/api";

export function UploadAnalyzer({ facilityId }: { facilityId: number }) {
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      setAnalysis(await api.uploadAnalyze(facilityId, file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">Image Analysis</h2>
          <p className="text-sm text-slate-500">Upload a current frame to estimate congestion.</p>
        </div>
        <button
          onClick={submit}
          disabled={!file || loading}
          className="focus-ring rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? "Analyzing..." : "Run analysis"}
        </button>
      </div>
      <input
        className="mt-5 block w-full rounded-lg border border-line bg-panel p-3 text-sm"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
      />
      {error ? <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      {analysis ? (
        <div className="mt-5 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="relative min-h-80 overflow-hidden rounded-lg bg-slate-100">
            {analysis.annotated_image_url || analysis.image_url ? (
              <Image
                src={analysis.annotated_image_url ?? analysis.image_url!}
                alt="Annotated analysis"
                fill
                unoptimized
                className="object-contain"
              />
            ) : null}
          </div>
          <div className="grid content-start gap-3">
            <CongestionBadge level={analysis.congestion_level} />
            <p className="text-4xl font-semibold text-ink">{percent(analysis.occupancy_rate)}</p>
            <p className="text-sm text-slate-500">Estimated occupancy from detected people and facility capacity.</p>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-panel p-3">
                <p className="text-xs text-slate-500">People</p>
                <p className="text-xl font-semibold">{analysis.people_count}</p>
              </div>
              <div className="rounded-lg bg-panel p-3">
                <p className="text-xs text-slate-500">Available</p>
                <p className="text-xl font-semibold">{analysis.available_seats}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

