import type { Analysis, AnalyticsOverview, Facility, FacilityStatus, HistoryPoint, LiveAnalysis } from "@/types/api";

const isServer = typeof window === "undefined";

export const API_BASE =
  (isServer
    ? process.env.INTERNAL_API_BASE_URL
    : process.env.NEXT_PUBLIC_API_BASE_URL) ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function safeErrorMessage(status: number, detail: unknown): string {
  const fallback = typeof detail === "string" && detail.trim() ? detail.trim() : null;

  if (status === 401) return "Please sign in to continue.";
  if (status === 403) return "You do not have permission to perform this action.";
  if (status === 404) return fallback ?? "The requested resource was not found.";
  if (status === 413) return "The selected image is too large.";
  if (status >= 500) return "The server could not complete this request. Please try again.";
  return fallback ?? `Request failed with status ${status}.`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    let detail: unknown = null;
    try {
      const payload = await response.json();
      detail = payload?.detail ?? payload?.message ?? null;
    } catch {
      detail = await response.text().catch(() => null);
    }
    throw new ApiError(response.status, safeErrorMessage(response.status, detail));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("smart-seat-token");
}

export function setToken(token: string): void {
  window.localStorage.setItem("smart-seat-token", token);
}

export function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  facilities: () => request<FacilityStatus[]>("/facilities"),
  facility: (id: number) => request<Facility>(`/facilities/${id}`),
  status: (id: number) => request<FacilityStatus>(`/facilities/${id}/status`),
  history: (id: number) => request<HistoryPoint[]>(`/facilities/${id}/history?limit=120`),
  analysis: (id: number) => request<Analysis>(`/analyses/${id}`),
  uploadAnalyze: (facilityId: number, file: File) => {
    const form = new FormData();
    form.append("facility_id", String(facilityId));
    form.append("file", file);
    return request<Analysis>("/uploads/analyze", {
      method: "POST",
      body: form,
      headers: authHeaders()
    });
  },
  liveAnalyze: (facilityId: number, file: Blob, persist: boolean) => {
    const form = new FormData();
    form.append("facility_id", String(facilityId));
    form.append("persist", String(persist));
    form.append("file", file, `live-frame-${Date.now()}.jpg`);
    return request<LiveAnalysis>("/live/analyze", {
      method: "POST",
      body: form,
      headers: authHeaders()
    });
  },
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  adminOverview: () => request<AnalyticsOverview>("/admin/analytics/overview", { headers: authHeaders() }),
  adminFacilities: () => request<Facility[]>("/admin/facilities", { headers: authHeaders() }),
  createFacility: (payload: Partial<Facility>) =>
    request<Facility>("/admin/facilities", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: authHeaders()
    }),
  updateFacility: (id: number, payload: Partial<Facility>) =>
    request<Facility>(`/admin/facilities/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
      headers: authHeaders()
    }),
  deleteFacility: (id: number) =>
    request<void>(`/admin/facilities/${id}`, {
      method: "DELETE",
      headers: authHeaders()
    })
};
