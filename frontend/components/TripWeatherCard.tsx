"use client";

import { weatherEmoji } from "@/lib/weather";
import type { TripWeather } from "@/lib/types";

interface TripWeatherCardProps {
  data: TripWeather | null;
  loading: boolean;
  fallback?: string | null;
}

export default function TripWeatherCard({
  data,
  loading,
  fallback,
}: TripWeatherCardProps) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-sky-100 bg-white p-4 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900">☀️ 行程天气</h3>
        <p className="mt-3 text-xs text-slate-400">天气加载中…</p>
      </div>
    );
  }

  if (!data && !fallback) return null;

  const days = data?.days ?? [];
  const hasRealWeather = days.length > 0;

  return (
    <div className="rounded-2xl border border-sky-100 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-1.5 text-sm font-bold text-slate-900">
          ☀️ 行程天气
        </h3>
        {data?.live && (
          <span className="text-xs text-sky-700">
            📍 {data.destination} 当前 {data.live.temperature}°C{" "}
            {data.live.weather}
          </span>
        )}
      </div>

      {hasRealWeather ? (
        <ul className="mt-3 space-y-1.5">
          {days.map((d) => (
            <li
              key={d.day}
              className="flex items-center gap-3 rounded-xl bg-sky-50/70 px-3 py-2 text-sm"
            >
              <span className="w-16 shrink-0 font-semibold text-slate-700">
                {formatDateLabel(d.date)}
              </span>
              <span className="text-base">{weatherEmoji(d.weather)}</span>
              <span className="min-w-0 flex-1 truncate text-slate-600">
                {d.weather || "—"}
              </span>
              <span className="shrink-0 text-xs text-slate-500">
                {d.temp_min ? `${d.temp_min}~${d.temp_max}°C` : "—"}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        fallback && (
          <p className="mt-3 rounded-xl bg-sky-50/70 px-3 py-2 text-sm text-sky-700">
            🌦 出行日天气：{fallback}
          </p>
        )
      )}

      {data && !data.within_window && (
        <p className="mt-2 text-xs text-slate-400">
          出发日期超过 4 天预报范围，出发前 3 天会自动更新实时预报
        </p>
      )}
    </div>
  );
}

function formatDateLabel(iso: string): string {
  const parts = iso.split("-");
  if (parts.length !== 3) return iso;
  return `${Number(parts[1])}月${Number(parts[2])}日`;
}
