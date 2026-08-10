"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import ItineraryList from "@/components/ItineraryList";
import MapView from "@/components/MapView";
import PlaceCard from "@/components/PlaceCard";
import TripBudgetCard from "@/components/TripBudgetCard";
import { ApiError, getToken, tripApi } from "@/lib/api";
import type { Place, ScheduleItem, Trip } from "@/lib/types";

const MOBILE_TABS = [
  { key: "itinerary", label: "行程" },
  { key: "map", label: "地图" },
  { key: "detail", label: "详情" },
] as const;

type MobileTab = (typeof MOBILE_TABS)[number]["key"];

export default function TripPlannerPage() {
  const params = useParams<{ id: string }>();
  const tripId = Number(params.id);
  const router = useRouter();

  const [trip, setTrip] = useState<Trip | null>(null);
  const [items, setItems] = useState<ScheduleItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mobileTab, setMobileTab] = useState<MobileTab>("itinerary");
  const [mapFocus, setMapFocus] = useState<{ id: number; nonce: number } | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    tripApi
      .get(tripId)
      .then((t) => {
        applyTrip(t);
        if (t.status === "draft") {
          setError("该行程尚未生成完成，请删除后重新创建");
        }
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) router.push("/login");
        else setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => setLoading(false));
  }, [tripId, router]);

  const selected = items.find((it) => it.id === selectedId) ?? null;

  function applyTrip(t: Trip) {
    setTrip(t);
    setItems(t.schedules);
    setSelectedId(t.schedules[0]?.id ?? null);
  }

  function handleSelect(id: number) {
    setSelectedId(id);
    setMobileTab("detail");
  }

  function handleViewOnMap(id: number) {
    setMapFocus((prev) => ({ id, nonce: (prev?.nonce ?? 0) + 1 }));
    setMobileTab("map");
  }

  function renumberDay(list: ScheduleItem[]): ScheduleItem[] {
    return list.map((it, idx) => ({ ...it, order_index: idx }));
  }

  function moveItem(id: number, dir: -1 | 1) {
    setItems((prev) => {
      const target = prev.find((it) => it.id === id);
      if (!target) return prev;
      const dayItems = prev.filter((it) => it.day === target.day);
      const pos = dayItems.findIndex((it) => it.id === id);
      const swapPos = pos + dir;
      if (swapPos < 0 || swapPos >= dayItems.length) return prev;
      [dayItems[pos], dayItems[swapPos]] = [dayItems[swapPos], dayItems[pos]];
      const renumbered = renumberDay(dayItems);
      return [...prev.filter((it) => it.day !== target.day), ...renumbered].sort(
        (a, b) => a.day - b.day || a.order_index - b.order_index
      );
    });
  }

  function removeItem(id: number) {
    setItems((prev) => {
      const target = prev.find((it) => it.id === id);
      if (!target) return prev;
      const rest = prev.filter((it) => it.id !== id);
      const dayList = renumberDay(rest.filter((it) => it.day === target.day));
      return [...rest.filter((it) => it.day !== target.day), ...dayList].sort(
        (a, b) => a.day - b.day || a.order_index - b.order_index
      );
    });
    if (selectedId === id) setSelectedId(null);
  }

  function updateItem(id: number, patch: Partial<ScheduleItem>) {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)));
  }

  function addPlace(day: number, place: Place) {
    const newId = -Date.now();
    setItems((prev) => {
      const dayItems = prev.filter((it) => it.day === day);
      const newItem: ScheduleItem = {
        id: newId,
        day,
        order_index: dayItems.length,
        place,
        recommended_time: null,
        duration_minutes: 120,
        cost_estimate: 0,
        transport: null,
        reason: null,
      };
      return [...prev, newItem].sort(
        (a, b) => a.day - b.day || a.order_index - b.order_index
      );
    });
    setSelectedId(newId);
  }

  async function save() {
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const payload = items.map((it) => ({
        day: it.day,
        order_index: it.order_index,
        place_id: it.place.id,
        recommended_time: it.recommended_time,
        duration_minutes: it.duration_minutes,
        cost_estimate: it.cost_estimate,
        transport: it.transport,
        reason: it.reason,
      }));
      const updated = await tripApi.updateSchedule(tripId, payload);
      applyTrip(updated);
      setEditMode(false);
      setNotice("修改已保存 ✓");
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function reoptimize() {
    setOptimizing(true);
    setError("");
    setNotice("");
    try {
      const res = await tripApi.reoptimize(tripId);
      applyTrip(res.trip);
      setEditMode(false);
      setNotice("AI 已重新优化路线 ✓");
    } catch (e) {
      setError(e instanceof Error ? e.message : "优化失败");
    } finally {
      setOptimizing(false);
    }
  }

  async function copyShareLink() {
    const url = `${window.location.origin}/trips/${tripId}/share`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setNotice(`复制失败，请手动复制：${url}`);
    }
  }

  if (loading) {
    return <p className="mt-16 text-center text-sm text-slate-400">加载中…</p>;
  }

  if (error || !trip) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="text-3xl">😵</p>
        <p className="mt-3 text-sm text-rose-600">{error ?? "旅行不存在"}</p>
        <Link href="/my-trips" className="mt-4 inline-block text-sm font-medium text-teal-600 hover:underline">
          返回我的旅行
        </Link>
      </div>
    );
  }

  const mapPlaces = items.map((it) => ({
    id: it.id,
    name: it.place.name,
    latitude: it.place.latitude,
    longitude: it.place.longitude,
    day: it.day,
    order_index: it.order_index,
  }));

  return (
    <div className="space-y-4 pb-24 lg:pb-0">
      {/* Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{trip.title}</h1>
            <div className="mt-2 flex flex-wrap gap-2 text-sm text-slate-500">
              <span>📍 {trip.destination}</span>
              <span>· {trip.start_date.slice(0, 10)} ~ {trip.end_date.slice(0, 10)}</span>
              <span>· {trip.travelers} 人</span>
              <span>· 预算 ¥{trip.budget}</span>
              <span>· 节奏：{trip.pace}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {editMode ? (
              <>
                <button
                  onClick={save}
                  disabled={saving}
                  className="rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
                >
                  {saving ? "保存中…" : "保存修改"}
                </button>
                <button
                  onClick={() => {
                    setEditMode(false);
                    setItems(trip.schedules);
                  }}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  取消
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setEditMode(true)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  ✏️ 编辑行程
                </button>
                <button
                  onClick={reoptimize}
                  disabled={optimizing}
                  className="rounded-xl border border-violet-200 bg-violet-50 px-4 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-100 disabled:opacity-60"
                >
                  {optimizing ? "优化中…" : "✨ AI 重新优化"}
                </button>
                <button
                  onClick={copyShareLink}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
                >
                  {copied ? "已复制 ✓" : "分享旅行"}
                </button>
              </>
            )}
          </div>
        </div>
        {(notice || error) && (
          <div
            className={`mt-3 rounded-xl px-4 py-2.5 text-sm ${
              error ? "bg-rose-50 text-rose-600" : "bg-teal-50 text-teal-700"
            }`}
          >
            {error || notice}
          </div>
        )}
      </div>

      {/* AI budget plan */}
      <TripBudgetCard trip={trip} />

      {/* Mobile: segmented tabs */}
      <div className="sticky top-16 z-30 -mx-4 border-b border-slate-200 bg-white/95 px-4 py-2 backdrop-blur lg:hidden">
        <div className="flex rounded-xl bg-slate-100 p-1">
          {MOBILE_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setMobileTab(tab.key)}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
                mobileTab === tab.key
                  ? "bg-white text-teal-700 shadow-sm"
                  : "text-slate-500"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Mobile panels */}
      <div className="space-y-4 lg:hidden">
        <div className={mobileTab === "itinerary" ? "block" : "hidden"}>
          <ItineraryList
            items={items}
            selectedId={selectedId}
            editMode={editMode}
            onSelect={handleSelect}
            onMove={moveItem}
            onRemove={removeItem}
            onAddPlace={addPlace}
            destination={trip.destination}
          />
        </div>
        <div className={mobileTab === "map" ? "block" : "hidden"}>
          <MapView
            places={mapPlaces}
            selectedId={selectedId}
            onSelect={handleSelect}
            focusId={mapFocus?.id ?? null}
            focusNonce={mapFocus?.nonce ?? 0}
            className="h-[62vh]"
          />
        </div>
        <div className={mobileTab === "detail" ? "block" : "hidden"}>
          <PlaceCard
            item={selected}
            editMode={editMode}
            onMove={moveItem}
            onRemove={removeItem}
            onUpdate={updateItem}
            onViewOnMap={() => selected && handleViewOnMap(selected.id)}
          />
        </div>
      </div>

      {/* Desktop three-column layout */}
      <div className="hidden grid-cols-1 gap-4 lg:grid lg:grid-cols-12">
        <div className="max-h-[70vh] overflow-y-auto pr-1 lg:col-span-4">
          <ItineraryList
            items={items}
            selectedId={selectedId}
            editMode={editMode}
            onSelect={handleSelect}
            onMove={moveItem}
            onRemove={removeItem}
            onAddPlace={addPlace}
            destination={trip.destination}
          />
        </div>

        <div className="lg:col-span-5">
          <MapView
            places={mapPlaces}
            selectedId={selectedId}
            onSelect={handleSelect}
            focusId={mapFocus?.id ?? null}
            focusNonce={mapFocus?.nonce ?? 0}
            className="h-[420px] lg:h-[calc(100vh-190px)] lg:sticky lg:top-24"
          />
        </div>

        <div className="lg:col-span-3">
          <PlaceCard
            item={selected}
            editMode={editMode}
            onMove={moveItem}
            onRemove={removeItem}
            onUpdate={updateItem}
            onViewOnMap={() => selected && handleViewOnMap(selected.id)}
          />
        </div>
      </div>

      {/* Mobile edit action bar */}
      {editMode && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 p-3 backdrop-blur lg:hidden">
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={saving}
              className="flex-1 rounded-xl bg-teal-600 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700 disabled:opacity-60"
            >
              {saving ? "保存中…" : "保存修改"}
            </button>
            <button
              onClick={() => {
                setEditMode(false);
                setItems(trip.schedules);
              }}
              className="flex-1 rounded-xl border border-slate-200 bg-white py-3 text-sm font-medium text-slate-600"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
