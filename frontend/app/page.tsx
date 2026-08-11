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
    <div className="space-y-10">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-600 via-emerald-600 to-cyan-600 px-5 py-8 text-white sm:rounded-3xl sm:px-10 sm:py-12">
        <div className="pointer-events-none absolute -right-8 -top-8 text-[7rem] opacity-10 sm:text-[11rem]">
          ✈
        </div>
        <div className="relative max-w-2xl">
          <h1 className="text-2xl font-extrabold leading-snug sm:text-4xl md:text-5xl">
            10 分钟，让 AI 帮你规划好一场旅行
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-sm text-teal-50/85 sm:text-base">
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
          <div className="mt-5 flex flex-col gap-2.5 sm:flex-row sm:items-center">
            <div className="flex flex-1 items-center gap-2 rounded-xl bg-white/95 px-3.5 py-3 shadow-md">
              <span className="shrink-0 text-base">📍</span>
              <input
                value={quickDest}
                onChange={(e) => setQuickDest(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && goCreate()}
                placeholder="想去哪？比如：上海、成都、大理"
                className="w-full bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={goCreate}
                className="whitespace-nowrap rounded-xl bg-white px-5 py-3 text-sm font-semibold text-teal-700 shadow-md transition hover:bg-teal-50 active:scale-[0.98]"
              >
                ✨ 开始规划
              </button>
              <Link
                href="#templates"
                className="whitespace-nowrap rounded-xl border border-white/35 px-4 py-3 text-sm font-medium text-white transition hover:bg-white/10"
              >
                推荐模板
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <span className="text-2xl">{f.icon}</span>
            <h3 className="mt-2 font-bold text-slate-900">{f.title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Templates */}
      <section id="templates">
        <h2 className="text-xl font-bold text-slate-900">推荐旅行模板</h2>
        <p className="mt-1 text-sm text-slate-500">
          一键带入目的地和兴趣偏好，快速开始。
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {TEMPLATES.map((t) => (
            <Link
              key={t.city}
              href={templateHref(t)}
              className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <span className="text-3xl">{t.emoji}</span>
              <h3 className="mt-2 text-lg font-bold text-slate-900">{t.city}</h3>
              <p className="text-sm text-slate-500">{t.days} 天经典路线</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {t.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs text-teal-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Recent trips */}
      {loggedIn && (
        <section>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900">最近旅行</h2>
            <Link href="/my-trips" className="text-sm font-medium text-teal-600 hover:underline">
              查看全部
            </Link>
          </div>
          {recentTrips.length === 0 ? (
            <p className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-400">
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
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
                >
                  <h3 className="font-bold text-slate-900">{t.title}</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {t.destination} · {t.start_date.slice(0, 10)} 起
                  </p>
                  <span className="mt-3 inline-block rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">
                    {t.schedules.length} 个地点
                  </span>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
