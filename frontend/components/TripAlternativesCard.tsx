"use client";

import type { Trip } from "@/lib/types";

export default function TripAlternativesCard({ trip }: { trip: Trip }) {
  const alternatives = trip.alternatives ?? [];
  if (alternatives.length === 0) return null;

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-5 shadow-sm">
      <h2 className="text-base font-bold text-slate-900">✨ 备选推荐（可选，由你决定）</h2>
      <p className="mt-1 text-xs text-slate-500">
        行程只是建议，以下项目可根据预算和时间自由选择加入或替换
      </p>
      <div className="mt-3 space-y-2">
        {alternatives.map((alt, i) => (
          <div
            key={i}
            className="rounded-xl border border-amber-100 bg-white px-3 py-2.5"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-slate-800">
                {alt.name}
              </span>
              {alt.cost_estimate != null && alt.cost_estimate > 0 && (
                <span className="text-sm font-semibold text-amber-600">
                  约 ¥{alt.cost_estimate}/人
                </span>
              )}
            </div>
            {alt.description && (
              <p className="mt-1 text-xs text-slate-500">{alt.description}</p>
            )}
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-400">
              {alt.day ? <span>建议第 {alt.day} 天</span> : null}
              {alt.replaces ? <span>可替换：{alt.replaces}</span> : null}
              {alt.reason ? <span>{alt.reason}</span> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
