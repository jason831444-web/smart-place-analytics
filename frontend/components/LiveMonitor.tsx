"use client";

import { CameraIcon, StopCircleIcon } from "@heroicons/react/24/outline";
import { useEffect, useRef, useState } from "react";

import { CongestionBadge } from "@/components/Badge";
import { api } from "@/lib/api";
import { percent, score, shortDate } from "@/lib/format";
import type { Facility, LiveAnalysis } from "@/types/api";

const FRAME_INTERVAL_MS = 3000;

function cameraErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError") return "Camera permission was denied. Allow camera access in the browser and try again.";
    if (error.name === "NotFoundError") return "No camera was found on this device.";
  }
  return "Unable to start the camera.";
}

export function LiveMonitor({ facility }: { facility: Facility }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number | null>(null);
  const analyzingRef = useRef(false);
  const framePreviewRef = useRef<string | null>(null);

  const [running, setRunning] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [persistLive, setPersistLive] = useState(true);
  const [result, setResult] = useState<LiveAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [framePreview, setFramePreview] = useState<string | null>(null);

  async function analyzeFrame() {
    if (analyzingRef.current || !videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    if (!video.videoWidth || !video.videoHeight) return;

    analyzingRef.current = true;
    setAnalyzing(true);
    setError(null);

    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      setError("Unable to read camera frame.");
      analyzingRef.current = false;
      setAnalyzing(false);
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.82));
    if (!blob) {
      setError("Unable to encode camera frame.");
      analyzingRef.current = false;
      setAnalyzing(false);
      return;
    }

    const nextPreviewUrl = URL.createObjectURL(blob);
    if (framePreviewRef.current) URL.revokeObjectURL(framePreviewRef.current);
    framePreviewRef.current = nextPreviewUrl;
    setFramePreview(nextPreviewUrl);

    try {
      setResult(await api.liveAnalyze(facility.id, blob, persistLive));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Live analysis failed.");
    } finally {
      analyzingRef.current = false;
      setAnalyzing(false);
    }
  }

  async function startCamera() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setRunning(true);
      void analyzeFrame();
      intervalRef.current = window.setInterval(() => void analyzeFrame(), FRAME_INTERVAL_MS);
    } catch (err) {
      setError(cameraErrorMessage(err));
    }
  }

  function stopCamera() {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setRunning(false);
    setAnalyzing(false);
    analyzingRef.current = false;
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if (framePreviewRef.current) URL.revokeObjectURL(framePreviewRef.current);
    };
  }, []);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-mint">Live monitoring</p>
            <h1 className="mt-2 text-3xl font-semibold text-ink">{facility.name}</h1>
            <p className="mt-1 text-sm text-slate-500">{facility.location} · {facility.total_seats} seats</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-slate-700">
              <input type="checkbox" checked={persistLive} onChange={(event) => setPersistLive(event.target.checked)} />
              Persist throttled samples
            </label>
            <button
              onClick={startCamera}
              disabled={running}
              className="focus-ring inline-flex items-center gap-2 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              <CameraIcon className="h-4 w-4" />
              Start camera
            </button>
            <button
              onClick={stopCamera}
              disabled={!running}
              className="focus-ring inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:text-slate-300"
            >
              <StopCircleIcon className="h-4 w-4" />
              Stop
            </button>
          </div>
        </div>
        {error ? <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="overflow-hidden rounded-lg border border-line bg-black shadow-soft">
          <video ref={videoRef} muted playsInline className="aspect-video w-full object-contain" />
          <canvas ref={canvasRef} className="hidden" />
        </div>
        <div className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-ink">Current Estimate</h2>
              <p className="mt-1 text-sm text-slate-500">
                {analyzing ? "Analyzing latest frame..." : result ? `Updated ${shortDate(result.created_at)}` : "Start camera to analyze frames."}
              </p>
            </div>
            {result ? <CongestionBadge level={result.congestion_level} /> : null}
          </div>
          {result ? (
            <div className="mt-5 grid gap-3">
              <div className="rounded-lg bg-panel p-4">
                <p className="text-sm font-medium text-slate-500">Occupancy rate</p>
                <p className="mt-2 text-3xl font-semibold text-ink">{percent(result.occupancy_rate)}</p>
                <p className="mt-1 text-sm text-slate-500">Score {score(result.congestion_score)}</p>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-panel p-3 text-center">
                  <p className="text-xs text-slate-500">People</p>
                  <p className="text-xl font-semibold text-ink">{result.people_count}</p>
                </div>
                <div className="rounded-lg bg-panel p-3 text-center">
                  <p className="text-xs text-slate-500">Occupied</p>
                  <p className="text-xl font-semibold text-ink">{result.occupied_seats}</p>
                </div>
                <div className="rounded-lg bg-panel p-3 text-center">
                  <p className="text-xs text-slate-500">Open</p>
                  <p className="text-xl font-semibold text-ink">{result.available_seats}</p>
                </div>
              </div>
              <div className="rounded-lg bg-panel p-3 text-sm text-slate-600">
                <p>Detector: {result.detector_backend} · {result.detector_model}</p>
                <p>{result.persisted ? "Saved to history." : result.persistence_requested ? `Next save available in ${result.next_persist_after_seconds}s.` : "Live-only sample, not saved."}</p>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      {framePreview ? (
        <section className="rounded-lg border border-line bg-white p-5 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">Last Submitted Frame</h2>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={framePreview} alt="Last submitted camera frame" className="mt-4 max-h-80 rounded-lg border border-line object-contain" />
        </section>
      ) : null}
    </div>
  );
}
