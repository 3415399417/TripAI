"use client";

import { useState } from "react";
import { tripApi } from "@/lib/api";
import type { Trip } from "@/lib/types";

export default function TripGenerationCard({ trip }: { trip: Trip }) {
  const [log, setLog] = useState<Record<string, unknown> | null>(null);
  const [showLog, setShowLog] = useState(false);
  const [loadingLog, setLoadingLog] = useState(false);

  const score = trip.score_detail ?? {};
  const hasScore = trip.score_total != null;
  if (!trip.weather && !hasScore && trip.llm_seconds == null) return null;

  async function toggleLog() {
    if (log) {
      setShowLog(!showLog);
      return;
    }
    setLoadingLog(true);
    try {
      setLog(await tripApi.getGenerationLog(trip.id));
      setShowLog(true);
    } catch {
      setLog({ detail: "日志加载失败" });
      setShowLog(true);
    } finally {
      setLoadingLog(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-bold text-slate-900">🤖 AI 生成报告</h2>
      <div className="mt-2 space-y-3 text-sm">
        {trip.weather && (
          <div className="rounded-xl bg-sky-50 px-3 py-2 text-sky-700">
            🌦 出行日天气：{trip.weather}，已按天气调整行程
          </div>
        )}

        {hasScore && (
          <div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">生成评分</span>
              <span className="font-bold text-slate-900">
                {trip.score_total}/100
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full rounded-full ${
                  (trip.score_total ?? 0) >= 75
                    ? "bg-emerald-500"
                    : (trip.score_total ?? 0) >= 60
                      ? "bg-amber-500"
                      : "bg-rose-500"
                }`}
                style={{ width: `${Math.min(100, trip.score_total ?? 0)}%` }}
              />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-slate-500">
              <span>预算匹配 {score.budget_match ?? "-"}</span>
              <span>兴趣匹配 {score.interest_match ?? "-"}</span>
              <span>路线合理 {score.route_reason ?? "-"}</span>
              <span>消费符合 {score.quality_match ?? "-"}</span>
            </div>
          </div>
        )}

        {trip.llm_seconds != null && (
          <p className="text-xs text-slate-400">
            ⏱ AI 生成耗时：{trip.llm_seconds} 秒
          </p>
        )}

        <div>
          <button
            onClick={toggleLog}
            className="text-xs font-medium text-teal-600 hover:underline"
          >
            {loadingLog
              ? "加载中..."
              : showLog
                ? "收起生成日志"
                : "查看生成日志（Prompt / AI 输出）"}
          </button>
          {showLog && log && (
            <pre className="mt-2 max-h-72 overflow-auto rounded-xl bg-slate-900 p-3 text-xs text-slate-100">
              {JSON.stringify(log, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
