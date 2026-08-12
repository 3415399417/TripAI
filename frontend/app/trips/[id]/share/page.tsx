"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import ItineraryList from "@/components/ItineraryList";
import MapView from "@/components/MapView";
import TripWeatherCard from "@/components/TripWeatherCard";
import { tripApi } from "@/lib/api";
import type { Trip, TripWeather, TripWeatherDay } from "@/lib/types";

export default function SharePage() {
  const params = useParams<{ id: string }>();
  const tripId = Number(params.id);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [weather, setWeather] = useState<TripWeather | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(true);

  useEffect(() => {
    tripApi
      .getPublic(tripId)
      .then(setTrip)
      .catch((e) => setError(e instanceof Error ? e.message : "分享页不存在"))
      .finally(() => setLoading(false));
  }, [tripId]);

  useEffect(() => {
    if (!trip) return;
    let cancelled = false;
    setWeatherLoading(true);
    tripApi
      .getPublicWeather(trip.id)
      .then((w) => {
        if (!cancelled) setWeather(w);
      })
      .catch(() => {
        if (!cancelled) setWeather(null);
      })
      .finally(() => {
        if (!cancelled) setWeatherLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [trip?.id]);

  const mapPlaces = useMemo(
    () =>
      (trip?.schedules ?? []).map((it) => ({
        id: it.id,
        name: it.place.name,
        latitude: it.place.latitude,
        longitude: it.place.longitude,
        day: it.day,
        order_index: it.order_index,
      })),
    [trip]
  );

  const dayWeather = useMemo(() => {
    const map: Record<number, TripWeatherDay> = {};
    (weather?.days ?? []).forEach((d) => {
      map[d.day] = d;
    });
    return map;
  }, [weather]);

  if (loading) return <p className="mt-16 text-center text-sm text-slate-400">加载中…</p>;

  if (error || !trip) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="text-3xl">🔗</p>
        <p className="mt-3 text-sm text-rose-600">{error ?? "分享页不存在"}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-gradient-to-r from-teal-600 to-emerald-600 p-6 text-white shadow-md">
        <p className="text-sm text-teal-100">TripAI 旅行分享</p>
        <h1 className="mt-1 text-3xl font-extrabold">{trip.title}</h1>
        <div className="mt-3 flex flex-wrap gap-3 text-sm text-teal-50">
          <span>📍 {trip.destination}</span>
          <span>· {trip.start_date.slice(0, 10)} ~ {trip.end_date.slice(0, 10)}</span>
          <span>· {trip.travelers} 人</span>
          <span>· 预算 ¥{trip.budget}</span>
          <span>· 节奏：{trip.pace}</span>
        </div>
      </div>

      <TripWeatherCard
        data={weather}
        loading={weatherLoading}
        fallback={trip.weather}
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <MapView
            places={mapPlaces}
            selectedId={null}
            onSelect={() => {}}
            className="h-[420px] lg:h-[520px]"
          />
        </div>
        <div className="max-h-[70vh] overflow-y-auto pr-1 lg:col-span-5">
          <ItineraryList
            key={trip.id}
            items={trip.schedules}
            selectedId={null}
            editMode={false}
            onSelect={() => {}}
            onMove={() => {}}
            onRemove={() => {}}
            onAddPlace={() => {}}
            destination={trip.destination}
            dayWeather={dayWeather}
          />
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 text-center shadow-sm">
        <p className="text-sm text-slate-500">
          喜欢这份行程？用 TripAI 免费生成你自己的旅行计划 →
        </p>
        <Link
          href="/"
          className="mt-3 inline-block rounded-xl bg-teal-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
        >
          开始创建
        </Link>
      </div>
    </div>
  );
}
