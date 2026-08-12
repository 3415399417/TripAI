"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, authApi, clearToken, getToken } from "@/lib/api";
import type { User, UserStats } from "@/lib/types";

export default function MePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [nickname, setNickname] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    Promise.all([authApi.me(), authApi.meStats()])
      .then(([u, s]) => {
        setUser(u);
        setNickname(u.nickname);
        setStats(s);
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) {
          clearToken();
          router.push("/login");
        } else {
          setError(e instanceof Error ? e.message : "加载失败");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  async function saveNickname() {
    const value = nickname.trim();
    if (!value) return;
    setSaving(true);
    try {
      const updated = await authApi.updateMe(value);
      setUser(updated);
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  function logout() {
    clearToken();
    router.push("/login");
  }

  if (loading) {
    return <p className="mt-16 text-center text-sm text-slate-400">加载中…</p>;
  }

  if (error || !user) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-2xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="text-3xl">😵</p>
        <p className="mt-3 text-sm text-rose-600">{error ?? "加载失败"}</p>
        <Link
          href="/login"
          className="mt-4 inline-block text-sm font-medium text-teal-600 hover:underline"
        >
          重新登录
        </Link>
      </div>
    );
  }

  const statsCards = [
    { label: "旅行计划", value: stats?.trip_count ?? 0, icon: "🧳" },
    {
      label: "累计预算",
      value: `¥${(stats?.total_budget ?? 0).toLocaleString()}`,
      icon: "💰",
    },
    {
      label: "实际花费",
      value: `¥${(stats?.total_spent ?? 0).toLocaleString()}`,
      icon: "🧾",
    },
    { label: "规划地点", value: stats?.total_places ?? 0, icon: "📍" },
  ];

  return (
    <div className="space-y-5">
      {/* Profile header */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="h-24 bg-gradient-to-r from-teal-500 via-emerald-500 to-cyan-600" />
        <div className="px-5 pb-5">
          <div className="-mt-10 flex items-end justify-between">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl border-4 border-white bg-gradient-to-br from-teal-500 to-emerald-600 text-3xl font-bold text-white shadow-md">
              {user.nickname.slice(0, 1) || "旅"}
            </div>
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="mb-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-50"
              >
                ✏️ 编辑昵称
              </button>
            ) : (
              <div className="mb-1 flex gap-1.5">
                <button
                  onClick={saveNickname}
                  disabled={saving}
                  className="rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-700 disabled:opacity-60"
                >
                  {saving ? "保存中…" : "保存"}
                </button>
                <button
                  onClick={() => {
                    setEditing(false);
                    setNickname(user.nickname);
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-500 hover:bg-slate-50"
                >
                  取消
                </button>
              </div>
            )}
          </div>

          <div className="mt-3">
            {editing ? (
              <input
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={64}
                className="input w-full max-w-xs"
                autoFocus
              />
            ) : (
              <h1 className="text-xl font-bold text-slate-900">{user.nickname}</h1>
            )}
            <p className="mt-1 text-sm text-slate-500">{user.email}</p>
            <p className="mt-0.5 text-xs text-slate-400">
              TripAI 用户 · 已加入 {stats?.member_days ?? 0} 天
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {statsCards.map((card) => (
          <div
            key={card.label}
            className="rounded-2xl border border-slate-200 bg-white p-4 text-center shadow-sm"
          >
            <p className="text-xl">{card.icon}</p>
            <p className="mt-1.5 text-base font-bold text-slate-900">
              {card.value}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Menu */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <Link
          href="/my-trips"
          className="flex items-center justify-between border-b border-slate-100 px-5 py-4 transition hover:bg-slate-50"
        >
          <span className="flex items-center gap-3 text-sm font-medium text-slate-700">
            <span className="text-lg">🧳</span> 我的旅行
          </span>
          <span className="text-slate-300">›</span>
        </Link>
        <Link
          href="/trips/new"
          className="flex items-center justify-between border-b border-slate-100 px-5 py-4 transition hover:bg-slate-50"
        >
          <span className="flex items-center gap-3 text-sm font-medium text-slate-700">
            <span className="text-lg">✨</span> 创建旅行
          </span>
          <span className="text-slate-300">›</span>
        </Link>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 px-5 py-4 text-left text-sm font-medium text-rose-600 transition hover:bg-rose-50"
        >
          <span className="text-lg">🚪</span> 退出登录
        </button>
      </div>

      <p className="text-center text-xs text-slate-400">
        TripAI v1.0 · AI 智能旅行规划
      </p>
    </div>
  );
}
