"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { tripApi } from "@/lib/api";
import type { TripCreate } from "@/lib/types";

const INTEREST_OPTIONS = [
  "自然风光",
  "人文历史",
  "美食",
  "购物",
  "亲子",
  "探险",
  "休闲度假",
  "摄影",
  "博物馆",
  "夜生活",
];

const PACE_OPTIONS = ["轻松", "适中", "紧凑"];

const STYLE_OPTIONS = [
  "城市探索",
  "蜜月",
  "商务出差",
  "家庭亲子",
  "独自旅行",
  "毕业旅行",
  "闺蜜出行",
  "情侣约会",
  "深度研学",
  "康养休闲",
];

const GROUP_OPTIONS = ["成人", "老人", "儿童", "情侣"];

const PROGRESS_STEPS = [
  { key: "budget", label: "预算分析" },
  { key: "llm", label: "AI 规划行程" },
  { key: "verify", label: "地点核对" },
  { key: "finalize", label: "生成方案" },
];

interface TripFormProps {
  initialDestination?: string;
  initialInterests?: string[];
}

export default function TripForm({
  initialDestination = "",
  initialInterests = [],
}: TripFormProps) {
  const router = useRouter();
  const [destination, setDestination] = useState(initialDestination);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [travelers, setTravelers] = useState(2);
  const [budget, setBudget] = useState(3000);
  const [pace, setPace] = useState("适中");
  const [interests, setInterests] = useState<string[]>(initialInterests);
  const [travelStyle, setTravelStyle] = useState("城市探索");
  const [travelerGroup, setTravelerGroup] = useState("成人");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState("");
  const [stage, setStage] = useState("");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!loading) return;
    setElapsed(0);
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [loading]);

  function toggleInterest(tag: string) {
    setInterests((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!destination.trim()) return setError("请填写目的地");
    if (!startDate || !endDate) return setError("请选择旅行日期");
    if (endDate < startDate) return setError("结束日期不能早于开始日期");

    const payload: TripCreate = {
      destination: destination.trim(),
      start_date: startDate,
      end_date: endDate,
      travelers,
      budget,
      pace,
      interests,
      travel_style: travelStyle,
      traveler_group: travelerGroup,
    };

    setLoading(true);
    setProgress("");
    setStage("");
    try {
      const res = await tripApi.generateStream(payload, (s, message) => {
        setStage(s);
        setProgress(message);
      });
      router.push(`/trips/${res.trip.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }

  const today = new Date().toISOString().slice(0, 10);
  const days =
    startDate && endDate && endDate >= startDate
      ? Math.max(
          1,
          Math.round(
            (new Date(endDate).getTime() - new Date(startDate).getTime()) /
              86400000
          ) + 1
        )
      : 1;
  const perPersonPerDay =
    budget > 0 && travelers > 0 ? Math.round(budget / travelers / days) : 0;

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
    >
      <div className="section-title">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-50 text-base">
          📍
        </span>
        行程信息与预算
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="目的地" full>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="例如：上海、成都、三亚"
            className="input"
          />
        </Field>

        <Field label="出行人数">
          <input
            type="number"
            min={1}
            max={50}
            value={travelers}
            onChange={(e) => setTravelers(Number(e.target.value))}
            className="input"
          />
        </Field>

        <Field label="开始日期">
          <input
            type="date"
            min={today}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="input"
          />
        </Field>

        <Field label="结束日期">
          <input
            type="date"
            min={startDate || today}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="input"
          />
        </Field>

        <Field label="总预算（元）" full>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={1000}
              max={100000}
              step={500}
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="flex-1"
            />
            <span className="w-24 shrink-0 rounded-xl border border-teal-200 bg-teal-50 px-2 py-2 text-center text-sm font-bold text-teal-700">
              ¥{budget.toLocaleString()}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {[3000, 8000, 15000, 30000, 50000].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setBudget(v)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                  budget === v
                    ? "bg-teal-600 text-white"
                    : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                }`}
              >
                ¥{v.toLocaleString()}
              </button>
            ))}
          </div>
          {perPersonPerDay > 0 && (
            <p className="mt-2 text-xs text-slate-400">
              人均日预算约 ¥{perPersonPerDay}/天
              <span className="ml-1 text-slate-300">
                （{travelers}人 × {days}天，城市消费水平会影响实际档位）
              </span>
            </p>
          )}
        </Field>
      </div>

      <div className="section-title">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-50 text-base">
          🎯
        </span>
        偏好与人群
      </div>
      <Field label="旅行节奏">
        <div className="flex gap-2">
          {PACE_OPTIONS.map((p) => (
            <button
              type="button"
              key={p}
              onClick={() => setPace(p)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                pace === p
                  ? "bg-teal-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </Field>

      <Field label="兴趣偏好（可多选）">
        <div className="flex flex-wrap gap-2">
          {INTEREST_OPTIONS.map((tag) => (
            <button
              type="button"
              key={tag}
              onClick={() => toggleInterest(tag)}
              className={`rounded-full border px-3 py-1.5 text-sm font-medium transition ${
                interests.includes(tag)
                  ? "border-teal-600 bg-teal-50 text-teal-700"
                  : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </Field>

      <Field label="旅行类型">
        <div className="flex flex-wrap gap-2">
          {STYLE_OPTIONS.map((s) => (
            <button
              type="button"
              key={s}
              onClick={() => setTravelStyle(s)}
              className={`rounded-full border px-3 py-1.5 text-sm font-medium transition ${
                travelStyle === s
                  ? "border-teal-600 bg-teal-50 text-teal-700"
                  : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </Field>

      <Field label="随行人群">
        <div className="flex flex-wrap gap-2">
          {GROUP_OPTIONS.map((g) => (
            <button
              type="button"
              key={g}
              onClick={() => setTravelerGroup(g)}
              className={`rounded-full border px-3 py-1.5 text-sm font-medium transition ${
                travelerGroup === g
                  ? "border-teal-600 bg-teal-50 text-teal-700"
                  : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </Field>

      {error && (
        <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {error}
        </p>
      )}

      {loading && (
        <div className="rounded-2xl border border-teal-100 bg-teal-50/70 p-4">
          <div className="flex items-center gap-3">
            {PROGRESS_STEPS.map((step, idx) => {
              const currentIdx = PROGRESS_STEPS.findIndex((s) => s.key === stage);
              const done = currentIdx > idx || stage === "done";
              const active = currentIdx === idx;
              return (
                <div key={step.key} className="flex flex-1 flex-col items-center gap-1">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold ${
                      done
                        ? "bg-teal-600 text-white"
                        : active
                          ? "border-2 border-teal-600 text-teal-700"
                          : "bg-slate-200 text-slate-400"
                    }`}
                  >
                    {done ? "✓" : idx + 1}
                  </span>
                  <span
                    className={`text-[10px] ${
                      done || active ? "text-teal-700" : "text-slate-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="mt-3 flex items-center gap-2 text-sm font-medium text-teal-800">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
            {progress || "AI 正在规划行程…"}
          </p>
          <p className="mt-1 text-xs text-teal-500">
            已用时 {elapsed} 秒 · 全程通常需要 30~90 秒，生成后会自动跳转
          </p>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 py-3.5 font-semibold text-white shadow-md transition hover:from-teal-700 hover:to-emerald-700 disabled:opacity-60"
      >
        {loading ? "AI 规划中，请稍候…" : "✨ 生成旅行方案"}
      </button>
      <p className="text-center text-xs text-slate-400">
        首次生成约需 1~3 分钟，AI 会为每个目的地规划真实地点，请耐心等待
      </p>
    </form>
  );
}

function Field({
  label,
  full = false,
  children,
}: {
  label: string;
  full?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className={`block ${full ? "sm:col-span-2" : ""}`}>
      <span className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </span>
      {children}
    </label>
  );
}
