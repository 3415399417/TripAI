"use client";

import type {
  AIGenerateResponse,
  Place,
  TokenResponse,
  Trip,
  TripCreate,
  TripExpense,
  TripExpenseSummary,
  TripWeather,
  User,
  UserPreferences,
  UserStats,
} from "@/lib/types";

// 同源代理：所有请求走 Vercel 的 /api/* 路由，避免浏览器直连后端跨域/网络问题
const API_BASE = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, "") ?? "";

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

interface ApiRequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const { timeoutMs = 45_000, ...fetchOptions } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((fetchOptions.headers as Record<string, string>) ?? {}),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
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

/** 读取 SSE 流：generate-trip-stream 使用。返回最终 result 事件。 */
async function apiFetchSSE<T>(
  path: string,
  body: unknown,
  onEvent: (stage: string, message: string) => void
): Promise<T> {
  const token = getToken();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 300_000);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (e) {
    clearTimeout(timeout);
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError("生成超时，请稍后重试", 408);
    }
    throw e;
  }
  clearTimeout(timeout);

  if (!res.ok) {
    let detail = `请求失败 (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      // keep default
    }
    throw new ApiError(detail, res.status);
  }
  if (!res.body) throw new ApiError("浏览器不支持流式响应", 500);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: T | undefined;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      let event = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (event === "stage") {
          onEvent(parsed.stage ?? "progress", parsed.message ?? "");
        } else if (event === "result") {
          result = parsed as T;
        } else if (event === "error") {
          throw new ApiError(parsed.detail ?? "生成失败，请重试", 500);
        }
      } catch (e) {
        if (e instanceof ApiError) throw e;
      }
    }
  }
  if (!result) throw new ApiError("生成失败，请重试", 500);
  return result;
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
  meStats: () => apiFetch<UserStats>("/api/auth/me/stats"),
  updateMe: (nickname: string) =>
    apiFetch<User>("/api/auth/me", {
      method: "PUT",
      body: JSON.stringify({ nickname }),
    }),
  getPreferences: () => apiFetch<UserPreferences>("/api/auth/me/preferences"),
  updatePreferences: (payload: {
    favorite_places?: string[];
    avoid_places?: string[];
  }) =>
    apiFetch<UserPreferences>("/api/auth/me/preferences", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  clearPreferences: () =>
    apiFetch<null>("/api/auth/me/preferences", { method: "DELETE" }),
};

export const tripApi = {
  list: () => apiFetch<Trip[]>("/api/trips"),
  get: (id: number) => apiFetch<Trip>(`/api/trips/${id}`),
  getPublic: (id: number) => apiFetch<Trip>(`/api/trips/${id}/public`),
  getWeather: (id: number) => apiFetch<TripWeather>(`/api/trips/${id}/weather`),
  getPublicWeather: (id: number) =>
    apiFetch<TripWeather>(`/api/trips/${id}/public/weather`),
  listExpenses: (id: number) =>
    apiFetch<TripExpenseSummary>(`/api/trips/${id}/expenses`),
  addExpense: (
    id: number,
    payload: {
      day: number | null;
      category: string;
      description: string | null;
      amount: number;
    }
  ) =>
    apiFetch<TripExpense>(`/api/trips/${id}/expenses`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteExpense: (id: number, expenseId: number) =>
    apiFetch<null>(`/api/trips/${id}/expenses/${expenseId}`, {
      method: "DELETE",
    }),
  getGenerationLog: (id: number) =>
    apiFetch<Record<string, unknown>>(`/api/trips/${id}/generation-log`),
  generate: (payload: TripCreate) =>
    apiFetch<AIGenerateResponse>("/api/ai/generate-trip", {
      method: "POST",
      body: JSON.stringify(payload),
      timeoutMs: 240_000,
    }),
  generateStream: (
    payload: TripCreate,
    onEvent: (stage: string, message: string) => void
  ) => apiFetchSSE<AIGenerateResponse>("/api/ai/generate-trip-stream", payload, onEvent),
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
  getDetail: (id: number) => apiFetch<Place>(`/api/places/${id}/detail`),
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
