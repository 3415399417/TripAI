"use client";

import { useState } from "react";
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function toggleInterest(tag: string) {
    setInterests((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");

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
    };

    setLoading(true);
    try {
      const res = await tripApi.generate(payload);
      if (res.mock) {
        setNotice(
          "当前为示例行程（未配置 LLM_API_KEY），可先体验完整流程，配置后即可生成真实行程。"
        );
      }
      router.push(`/trips/${res.trip.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }

  const today = new Date().toISOString().slice(0, 10);

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
    >
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
          <input
            type="number"
            min={0}
            step={100}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="input"
          />
        </Field>
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

      {error && (
        <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {error}
        </p>
      )}
      {notice && (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
          {notice}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 py-3.5 font-semibold text-white shadow-md transition hover:from-teal-700 hover:to-emerald-700 disabled:opacity-60"
      >
        {loading ? "AI 规划中，请稍候…" : "✨ 生成旅行方案"}
      </button>
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

