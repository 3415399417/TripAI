"use client";

import { useMemo, useState } from "react";
import { placeApi } from "@/lib/api";
import type { Place, ScheduleItem } from "@/lib/types";

interface ItineraryListProps {
  items: ScheduleItem[];
  selectedId: number | null;
  editMode: boolean;
  onSelect: (id: number) => void;
  onMove: (id: number, dir: -1 | 1) => void;
  onRemove: (id: number) => void;
  onAddPlace: (day: number, place: Place) => void;
  destination: string;
}

export default function ItineraryList({
  items,
  selectedId,
  editMode,
  onSelect,
  onMove,
  onRemove,
  onAddPlace,
  destination,
}: ItineraryListProps) {
  const days = useMemo(() => {
    const map = new Map<number, ScheduleItem[]>();
    items.forEach((it) => {
      const list = map.get(it.day) ?? [];
      list.push(it);
      map.set(it.day, list);
    });
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [items]);

  return (
    <div className="space-y-4">
      {days.map(([day, list]) => (
        <section key={day} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="flex items-center gap-2 font-bold text-slate-900">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-600 text-sm text-white">
                {day}
              </span>
              第 {day} 天
            </h3>
            <span className="text-xs text-slate-400">{list.length} 个地点</span>
          </div>

          <ol className="relative space-y-2">
            {list.map((it, idx) => (
              <li key={it.id} className="relative">
                <button
                  onClick={() => onSelect(it.id)}
                  className={`w-full rounded-xl border p-3 text-left transition ${
                    selectedId === it.id
                      ? "border-teal-500 bg-teal-50/60"
                      : "border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        selectedId === it.id
                          ? "bg-teal-600 text-white"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {idx + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-slate-800">
                        {it.place.name}
                      </p>
                      <p className="mt-0.5 truncate text-xs text-slate-400">
                        {[it.recommended_time, it.place.category]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    </div>
                    {editMode && (
                      <span className="flex shrink-0 gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onMove(it.id, -1);
                          }}
                          disabled={idx === 0}
                          className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50 disabled:opacity-30"
                          title="上移"
                        >
                          ↑
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onMove(it.id, 1);
                          }}
                          disabled={idx === list.length - 1}
                          className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50 disabled:opacity-30"
                          title="下移"
                        >
                          ↓
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onRemove(it.id);
                          }}
                          className="rounded-md border border-rose-200 px-2 py-1 text-xs text-rose-500 hover:bg-rose-50"
                          title="删除"
                        >
                          ✕
                        </button>
                      </span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ol>

          {editMode && <AddPlaceBox day={day} destination={destination} onAdd={onAddPlace} />}
        </section>
      ))}
    </div>
  );
}

function AddPlaceBox({
  day,
  destination,
  onAdd,
}: {
  day: number;
  destination: string;
  onAdd: (day: number, place: Place) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  async function doSearch() {
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    try {
      setResults(await placeApi.search(query.trim(), destination));
    } catch (e) {
      setError(e instanceof Error ? e.message : "搜索失败");
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mt-3 w-full rounded-xl border border-dashed border-slate-300 py-2 text-sm font-medium text-teal-600 hover:border-teal-400 hover:bg-teal-50/50"
      >
        + 添加地点
      </button>
    );
  }

  return (
    <div className="mt-3 rounded-xl bg-slate-50 p-3">
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
          placeholder="搜索地点，如：外滩"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none"
        />
        <button
          onClick={doSearch}
          disabled={searching}
          className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
        >
          {searching ? "搜索中…" : "搜索"}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}
      {results.length > 0 && (
        <ul className="mt-2 max-h-56 space-y-1 overflow-y-auto">
          {results.map((p) => (
            <li key={p.id}>
              <button
                onClick={() => {
                  onAdd(day, p);
                  setResults([]);
                  setQuery("");
                  setOpen(false);
                }}
                className="w-full rounded-lg px-2 py-2 text-left hover:bg-white"
              >
                <p className="text-sm font-medium text-slate-700">{p.name}</p>
                <p className="truncate text-xs text-slate-400">
                  {[p.category, p.address].filter(Boolean).join(" · ")}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}
      <button
        onClick={() => setOpen(false)}
        className="mt-2 text-xs text-slate-400 hover:text-slate-600"
      >
        收起
      </button>
    </div>
  );
}

