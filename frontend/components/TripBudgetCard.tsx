"use client";

import type { Trip } from "@/lib/types";

const LEVEL_STYLES: Record<string, string> = {
  "经济型": "border-teal-200 bg-teal-50 text-teal-700",
  "舒适型": "border-sky-200 bg-sky-50 text-sky-700",
  "高品质": "border-violet-200 bg-violet-50 text-violet-700",
  "奢华型": "border-amber-200 bg-amber-50 text-amber-700",
};

const BREAKDOWN_ORDER = [
  "住宿",
  "餐饮",
  "交通",
  "景点门票",
  "娱乐体验",
  "购物",
  "备用资金",
];

export default function TripBudgetCard({ trip }: { trip: Trip }) {
  if (!trip.consumption_level) return null;

  const breakdown = trip.budget_breakdown ?? {};
  const total = Object.values(breakdown).reduce((sum, v) => sum + Number(v || 0), 0) || 1;
  const entries = BREAKDOWN_ORDER.filter((key) => breakdown[key] != null);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-base font-bold text-slate-900">
          {trip.traveler_profile || "AI 旅行画像"}
        </h2>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
            LEVEL_STYLES[trip.consumption_level] ??
            "border-slate-200 bg-slate-100 text-slate-600"
          }`}
        >
          {trip.consumption_level}
        </span>
      </div>

      {trip.budget_min != null && trip.budget_max != null && (
        <p className="mt-1 text-sm text-slate-500">
          建议消费区间 ¥{trip.budget_min} ~ ¥{trip.budget_max}
          <span className="mx-1 text-slate-300">|</span>
          总预算 ¥{trip.budget}
          <span className="text-slate-400">（预算不等于必须花完，剩余作为弹性资金）</span>
        </p>
      )}

      {entries.length > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {entries.map((key) => {
            const amount = Number(breakdown[key]) || 0;
            const pct = Math.min(100, Math.round((amount / total) * 100));
            return (
              <div key={key} className="rounded-xl bg-slate-50 px-3 py-2">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{key}</span>
                  <span className="font-semibold text-slate-700">¥{amount}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-teal-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
