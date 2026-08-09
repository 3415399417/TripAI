"use client";

import Link from "next/link";
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
  const [recentTrips, setRecentTrips] = useState<Trip[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);

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

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-teal-600 via-emerald-600 to-cyan-600 px-6 py-16 text-white sm:px-12">
        <div className="pointer-events-none absolute -right-20 -top-20 text-[16rem] opacity-15">
          ✈
        </div>
        <div className="relative max-w-2xl">
          <h1 className="text-3xl font-extrabold leading-tight sm:text-5xl">
            10 分钟，让 AI 帮你规划好一场旅行
          </h1>
          <p className="mt-4 text-lg text-teal-50/90">
            输入需求 → AI 生成行程 → 地图查看路线 → 编辑保存 → 分享给朋友
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/trips/new"
              className="rounded-xl bg-white px-6 py-3 font-semibold text-teal-700 shadow-lg transition hover:bg-teal-50"
            >
              ✨ 开始创建旅行
            </Link>
            <Link
              href="#templates"
              className="rounded-xl border border-white/40 px-6 py-3 font-semibold text-white transition hover:bg-white/10"
            >
              看看推荐模板
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <span className="text-3xl">{f.icon}</span>
            <h3 className="mt-3 font-bold text-slate-900">{f.title}</h3>
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
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {TEMPLATES.map((t) => (
            <Link
              key={t.city}
              href={templateHref(t)}
              className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <span className="text-4xl">{t.emoji}</span>
              <h3 className="mt-3 text-lg font-bold text-slate-900">{t.city}</h3>
              <p className="text-sm text-slate-500">{t.days} 天经典路线</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
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
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
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

