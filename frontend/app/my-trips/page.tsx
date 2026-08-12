"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, getToken, tripApi } from "@/lib/api";
import type { Trip } from "@/lib/types";

export default function MyTripsPage() {
  const router = useRouter();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    tripApi
      .list()
      .then(setTrips)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) router.push("/login");
        else setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function removeTrip(id: number) {
    if (!confirm("确定删除这个旅行计划吗？")) return;
    try {
      await tripApi.remove(id);
      setTrips((prev) => prev.filter((t) => t.id !== id));
    } catch (e) {
      alert(e instanceof Error ? e.message : "删除失败");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-header">我的旅行</h1>
          <p className="mt-1 text-sm text-slate-500">管理你所有的旅行计划</p>
        </div>
        <Link
          href="/trips/new"
          className="rounded-full bg-gradient-to-r from-teal-600 to-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-teal-600/25 transition hover:opacity-90"
        >
          + 新建旅行
        </Link>
      </div>

      {loading ? (
        <p className="mt-10 text-center text-sm text-slate-400">加载中…</p>
      ) : error ? (
        <p className="mt-10 text-center text-sm text-rose-600">{error}</p>
      ) : trips.length === 0 ? (
        <div className="mt-10 rounded-3xl border border-dashed border-slate-300 bg-white/60 p-12 text-center">
          <p className="text-4xl">🧳</p>
          <p className="mt-4 font-medium text-slate-600">还没有旅行计划</p>
          <p className="mt-1 text-sm text-slate-400">
            创建第一个，让 AI 帮你规划路线
          </p>
          <Link
            href="/trips/new"
            className="mt-6 inline-block rounded-xl bg-teal-600 px-6 py-3 font-semibold text-white hover:bg-teal-700"
          >
            创建旅行
          </Link>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {trips.map((t) => (
            <div
              key={t.id}
              className="group card card-interactive overflow-hidden"
            >
              <Link href={`/trips/${t.id}`}>
                <div className="flex h-24 items-start justify-between bg-gradient-to-br from-teal-500 via-emerald-500 to-cyan-600 px-5 py-4">
                  <div>
                    <span className="text-xl font-extrabold text-white">
                      {t.destination}
                    </span>
                    <p className="mt-0.5 text-xs text-white/80">
                      {t.start_date.slice(0, 10)} ~ {t.end_date.slice(0, 10)}
                    </p>
                  </div>
                  <span className="text-2xl opacity-70">🗺️</span>
                  {t.consumption_level && (
                    <span className="rounded-full bg-white/20 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur">
                      {t.consumption_level}
                    </span>
                  )}
                </div>
                <div className="p-5">
                  <h3 className="font-bold text-slate-900 transition group-hover:text-teal-700">
                    {t.title}
                  </h3>
                  <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-xs">
                    <span className="rounded-full bg-teal-50 px-2.5 py-1 font-medium text-teal-700">
                      {t.schedules.length} 个地点
                    </span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-500">
                      {t.travelers} 人
                    </span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-500">
                      ¥{t.budget.toLocaleString()}
                    </span>
                    {t.travel_style && (
                      <span className="rounded-full bg-amber-50 px-2.5 py-1 text-amber-700">
                        {t.travel_style}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
              <div className="mx-5 mb-5 flex gap-2 border-t border-slate-100 pt-3">
                <Link
                  href={`/trips/${t.id}`}
                  className="flex-1 rounded-lg border border-slate-200 py-1.5 text-center text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  查看/编辑
                </Link>
                <Link
                  href={`/trips/${t.id}/share`}
                  className="flex-1 rounded-lg border border-slate-200 py-1.5 text-center text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  分享页
                </Link>
                <button
                  onClick={() => removeTrip(t.id)}
                  className="rounded-lg border border-rose-200 px-3 py-1.5 text-sm font-medium text-rose-500 hover:bg-rose-50"
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
