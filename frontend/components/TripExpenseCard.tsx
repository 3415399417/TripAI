"use client";

import { useCallback, useEffect, useState } from "react";
import { tripApi } from "@/lib/api";
import type { TripExpenseSummary } from "@/lib/types";

const CATEGORIES = ["交通", "餐饮", "住宿", "门票", "购物", "娱乐", "其他"];

export default function TripExpenseCard({
  tripId,
  budget,
}: {
  tripId: number;
  budget: number;
}) {
  const [summary, setSummary] = useState<TripExpenseSummary | null>(null);
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("餐饮");
  const [day, setDay] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(() => {
    tripApi
      .listExpenses(tripId)
      .then(setSummary)
      .catch(() => setSummary(null));
  }, [tripId]);

  useEffect(() => {
    load();
  }, [load]);

  const spent = summary?.spent ?? 0;
  const remaining = summary?.remaining ?? budget;
  const pct = budget > 0 ? Math.min(100, Math.round((spent / budget) * 100)) : 0;

  async function add() {
    const value = Number(amount);
    if (!value || value <= 0) {
      setError("请输入有效金额");
      return;
    }
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await tripApi.addExpense(tripId, {
        amount: value,
        category,
        day: day ? Number(day) : null,
        description: description.trim() || null,
      });
      setAmount("");
      setDescription("");
      setDay("");
      await load();
      setNotice("已记录 ✓");
    } catch (e) {
      setError(e instanceof Error ? e.message : "记录失败");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: number) {
    try {
      await tripApi.deleteExpense(tripId, id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "删除失败");
    }
  }

  return (
    <div className="card p-5">
      <h2 className="text-base font-bold text-slate-900">💰 真实花费记账</h2>

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-xl bg-slate-50 px-2 py-2.5">
          <p className="text-[11px] text-slate-400">预算</p>
          <p className="mt-0.5 text-sm font-bold text-slate-800">
            ¥{Math.round(budget).toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl bg-teal-50 px-2 py-2.5">
          <p className="text-[11px] text-teal-600">已花费</p>
          <p className="mt-0.5 text-sm font-bold text-teal-700">
            ¥{Math.round(spent).toLocaleString()}
          </p>
        </div>
        <div
          className={`rounded-xl px-2 py-2.5 ${
            remaining > 0 ? "bg-emerald-50" : "bg-rose-50"
          }`}
        >
          <p className={`text-[11px] ${remaining > 0 ? "text-emerald-600" : "text-rose-500"}`}>
            结余
          </p>
          <p
            className={`mt-0.5 text-sm font-bold ${
              remaining > 0 ? "text-emerald-700" : "text-rose-600"
            }`}
          >
            ¥{Math.round(remaining).toLocaleString()}
          </p>
        </div>
      </div>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all ${
            pct >= 90 ? "bg-rose-500" : pct >= 60 ? "bg-amber-500" : "bg-teal-500"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-1 text-right text-[11px] text-slate-400">已使用预算 {pct}%</p>

      <div className="mt-4 space-y-2">
        <div className="flex flex-wrap gap-2">
          <input
            type="number"
            inputMode="decimal"
            min={0}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="金额（元）"
            className="input min-w-0 flex-1"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="input w-auto rounded-xl border border-slate-200 px-3 py-2 text-sm"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <input
            type="number"
            min={1}
            max={31}
            value={day}
            onChange={(e) => setDay(e.target.value)}
            placeholder="第几天"
            className="input w-20"
          />
        </div>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="备注，如：高铁票、外滩晚餐"
          className="input w-full"
        />
        <button
          onClick={add}
          disabled={saving}
          className="w-full rounded-xl bg-teal-600 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:opacity-60"
        >
          {saving ? "记录中…" : "+ 记一笔"}
        </button>
      </div>

      {(error || notice) && (
        <p
          className={`mt-3 rounded-xl px-3 py-2 text-xs ${
            error ? "bg-rose-50 text-rose-600" : "bg-teal-50 text-teal-700"
          }`}
        >
          {error || notice}
        </p>
      )}

      {summary && summary.items.length > 0 && (
        <ul className="mt-4 space-y-1.5 border-t border-slate-100 pt-3">
          {summary.items.map((it) => (
            <li
              key={it.id}
              className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm"
            >
              <span className="shrink-0 rounded-full bg-teal-100 px-2 py-0.5 text-[11px] font-medium text-teal-700">
                {it.category}
              </span>
              {it.day != null && (
                <span className="shrink-0 text-xs text-slate-400">D{it.day}</span>
              )}
              <span className="min-w-0 flex-1 truncate text-slate-600">
                {it.description ?? "—"}
              </span>
              <span className="shrink-0 font-semibold text-slate-800">
                ¥{Math.round(it.amount).toLocaleString()}
              </span>
              <button
                onClick={() => remove(it.id)}
                className="shrink-0 text-slate-300 hover:text-rose-500"
                aria-label="删除"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
