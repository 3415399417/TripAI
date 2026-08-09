"use client";

import type {
  AIGenerateResponse,
  Place,
  TokenResponse,
  Trip,
  TripCreate,
  User,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("tripai_token");
}

export function setToken(token: string): void {
  window.localStorage.setItem("tripai_token", token);
}

export function clearToken(): void {
  window.localStorage.removeItem("tripai_token");
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError("请求超时，请检查网络后重试", 408);
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
  if (!res.ok) {
    let detail = `请求失败 (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (data.detail) detail = JSON.stringify(data.detail);
    } catch {
      // keep default message
    }
    throw new ApiError(detail, res.status);
  }
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const authApi = {
  register: (email: string, password: string, nickname: string) =>
    apiFetch<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, nickname }),
    }),
  login: (email: string, password: string) =>
    apiFetch<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => apiFetch<User>("/api/auth/me"),
};

export const tripApi = {
  list: () => apiFetch<Trip[]>("/api/trips"),
  get: (id: number) => apiFetch<Trip>(`/api/trips/${id}`),
  getPublic: (id: number) => apiFetch<Trip>(`/api/trips/${id}/public`),
  generate: (payload: TripCreate) =>
    apiFetch<AIGenerateResponse>("/api/ai/generate-trip", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reoptimize: (tripId: number, instruction?: string) =>
    apiFetch<AIGenerateResponse>("/api/ai/reoptimize", {
      method: "POST",
      body: JSON.stringify({ trip_id: tripId, instruction: instruction ?? null }),
    }),
  updateSchedule: (tripId: number, items: ScheduleUpsertItem[]) =>
    apiFetch<Trip>(`/api/trips/${tripId}/schedule`, {
      method: "PUT",
      body: JSON.stringify(items),
    }),
  remove: (tripId: number) =>
    apiFetch<null>(`/api/trips/${tripId}`, { method: "DELETE" }),
};

export const placeApi = {
  search: (q: string, city?: string) =>
    apiFetch<Place[]>(
      `/api/places/search?q=${encodeURIComponent(q)}${
        city ? `&city=${encodeURIComponent(city)}` : ""
      }`
    ),
};

export interface ScheduleUpsertItem {
  day: number;
  order_index: number;
  place_id: number;
  recommended_time: string | null;
  duration_minutes: number;
  cost_estimate: number;
  transport: string | null;
  reason: string | null;
}

export function formatDate(iso: string): string {
  return iso.slice(0, 10);
}
