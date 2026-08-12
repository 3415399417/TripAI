"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, tripApi } from "@/lib/api";
import type { Trip } from "@/lib/types";

const FEATURES = [
  {
    icon: "🧠",
    title: "AI 智能规划",
    desc: "输入目的地、日期、预算和偏好，AI 自动生成每日行程。",
  },
  {
    icon: "🗺️",
    title: "地图可视化",
    desc: "所有地点在地图上标记连线，路线一目了然。",
  },
  {
    icon: "✏️",
    title: "自由编辑",
    desc: "拖拽调整顺序、增删地点，还能让 AI 重新优化路线。",
  },
  {
    icon: "🔗",
    title: "一键分享",
    desc: "生成公开分享页，把旅行计划发给朋友。",
  },
];

const TEMPLATES = [
  { city: "北京", days: 4, tags: ["人文历史", "美食"], emoji: "🏛️" },
  { city: "成都", days: 3, tags: ["美食", "休闲度假"], emoji: "🐼" },
  { city: "三亚", days: 4, tags: ["自然风光", "休闲度假"], emoji: "🏖️" },
  { city: "西安", days: 3, tags: ["人文历史", "美食"], emoji: "🏯" },
];

const HOT_CITIES = ["上海", "北京", "成都", "三亚", "杭州", "西安"];

export default function HomePage() {
  const router = useRouter();
  const [recentTrips, setRecentTrips] = useState<Trip[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);
  const [quickDest, setQuickDest] = useState("");

  useEffect(() => {
    if (!getToken()) return;
    setLoggedIn(true);
    tripApi
      .list()
      .then((list) => setRecentTrips(list.slice(0, 3)))
      .catch(() => {});
  }, []);

  const templateHref = (t: (typeof TEMPLATES)[number]) =>
    `/trips/new?destination=${encodeURIComponent(t.city)}&interests=${encodeURIComponent(
      t.tags.join(",")
    )}`;

  function goCreate() {
    const dest = quickDest.trim();
    router.push(
      dest
        ? `/trips/new?destination=${encodeURIComponent(dest)}`
        : "/trips/new"
    );
  }

  return (
    <div className="space-y-8 sm:space-y-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-teal-600 via-emerald-600 to-cyan-600 px-5 py-10 text-white shadow-xl shadow-teal-600/20 sm:px-10 sm:py-14">
        <div className="pointer-events-none absolute -right-10 -top-10 h-52 w-52 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-10 h-64 w-64 rounded-full bg-cyan-300/20 blur-3xl" />
        <div className="pointer-events-none absolute right-6 top-8 hidden text-[6rem] opacity-10 sm:block">
          ✈️
        </div>
        <div className="relative max-w-2xl">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur">
            ✨ AI 智能旅行规划
          </span>
          <h1 className="mt-4 text-3xl font-extrabold leading-tight sm:text-4xl md:text-5xl">
            10 分钟，让 AI 帮你规划好一场旅行
          </h1>
          <p className="mt-3 text-sm text-teal-50/90 sm:text-base">
            输入目的地、预算和喜好，自动生成每日行程、地图路线和花费预算
          </p>
          <div className="mt-4 hidden flex-wrap items-center gap-x-1.5 gap-y-0.5 text-sm text-teal-50/85 sm:flex">
            <span>输入需求</span>
            <span className="text-teal-200">→</span>
            <span>AI 生成行程</span>
            <span className="text-teal-200">→</span>
            <span>地图查看路线</span>
            <span className="text-teal-200 hidden sm:inline">→</span>
            <span className="hidden sm:inline">编辑保存</span>
            <span className="text-teal-200 hidden sm:inline">→</span>
            <span className="hidden sm:inline">分享给朋友</span>
          </div>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="flex flex-1 items-center gap-2.5 rounded-2xl bg-white/95 px-4 py-3.5 shadow-lg shadow-black/5 backdrop-blur">
              <span className="shrink-0 text-base">📍</span>
              <input
                value={quickDest}
                onChange={(e) => setQuickDest(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && goCreate()}
                placeholder="想去哪？比如：上海、成都、大理"
                className="w-full bg-transparent text-sm font-medium text-slate-700 placeholder:text-slate-400 focus:outline-none"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={goCreate}
                className="whitespace-nowrap rounded-2xl bg-white px-6 py-3.5 text-sm font-bold text-teal-700 shadow-lg shadow-black/10 transition hover:bg-teal-50 active:scale-[0.98]"
              >
                ✨ 开始规划
              </button>
              <Link
                href="#templates"
                className="whitespace-nowrap rounded-2xl border border-white/30 px-5 py-3.5 text-sm font-medium text-white backdrop-blur transition hover:bg-white/10"
              >
                推荐模板
              </Link>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-teal-50/75">热门：</span>
            {HOT_CITIES.map((city) => (
              <button
                key={city}
                onClick={() =>
                  router.push(`/trips/new?destination=${encodeURIComponent(city)}`)
                }
                className="rounded-full bg-white/12 px-3 py-1 text-xs font-medium text-white backdrop-blur transition hover:bg-white/25"
              >
                {city}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-2 gap-3">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="card card-interactive p-5"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-50 to-emerald-100 text-xl">
              {f.icon}
            </span>
            <h3 className="mt-3 font-bold text-slate-900">{f.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Templates */}
      <section id="templates">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="page-header">推荐旅行模板</h2>
            <p className="mt-1 text-sm text-slate-500">
              一键带入目的地和兴趣偏好，快速开始。
            </p>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3">
          {TEMPLATES.map((t) => (
            <Link
              key={t.city}
              href={templateHref(t)}
              className="group card card-interactive overflow-hidden"
            >
              <div className="flex items-center justify-between bg-gradient-to-br from-teal-500/10 to-emerald-500/10 px-5 pb-3 pt-5">
                <span className="text-4xl drop-shadow-sm">{t.emoji}</span>
                <span className="rounded-full bg-teal-600/10 px-2.5 py-1 text-xs font-semibold text-teal-700">
                  {t.days} 天
                </span>
              </div>
              <div className="px-5 pb-5">
                <h3 className="text-lg font-bold text-slate-900">{t.city}</h3>
                <p className="text-sm text-slate-500">经典路线推荐</p>
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {t.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Recent trips */}
      {loggedIn && (
        <section>
          <div className="flex items-center justify-between">
            <h2 className="page-header">最近旅行</h2>
            <Link href="/my-trips" className="text-sm font-medium text-teal-600 hover:underline">
              查看全部
            </Link>
          </div>
          {recentTrips.length === 0 ? (
            <p className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white/60 p-8 text-center text-sm text-slate-400">
              还没有旅行计划，去{" "}
              <Link href="/trips/new" className="text-teal-600 underline">
                创建第一个
              </Link>{" "}
              吧
            </p>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {recentTrips.map((t) => (
                <Link
                  key={t.id}
                  href={`/trips/${t.id}`}
                  className="card card-interactive overflow-hidden"
                >
                  <div className="flex h-16 items-center justify-between bg-gradient-to-br from-teal-500 to-emerald-600 px-5">
                    <span className="text-lg font-bold text-white">
                      {t.destination}
                    </span>
                    <span className="text-white/80">🗺️</span>
                  </div>
                  <div className="p-5">
                    <h3 className="truncate font-bold text-slate-900">
                      {t.title}
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {t.start_date.slice(0, 10)} 起
                    </p>
                    <span className="mt-3 inline-block rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">
                      {t.schedules.length} 个地点
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
