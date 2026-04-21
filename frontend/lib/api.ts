import type { Analysis, AnalyticsOverview, Facility, FacilityStatus, HistoryPoint } from "@/types/api";

const isServer = typeof window === "undefined";

export const API_BASE =
  (isServer
    ? process.env.INTERNAL_API_BASE_URL
    : process.env.NEXT_PUBLIC_API_BASE_URL) ?? "http://localhost:8000/api";

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
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
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