"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, authApi, clearToken, getToken } from "@/lib/api";
import type { User, UserPreferences, UserStats } from "@/lib/types";

export default function MePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
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
    Promise.all([authApi.me(), authApi.meStats(), authApi.getPreferences()])
      .then(([u, s, p]) => {
        setUser(u);
        setNickname(u.nickname);
        setStats(s);
        setPrefs(p);
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

  async function removePref(name: string, kind: "favorite" | "avoid") {
    if (!prefs) return;
    const favorites =
      kind === "favorite"
        ? prefs.favorite_places.filter((n) => n !== name)
        : prefs.favorite_places;
    const avoids =
      kind === "avoid"
        ? prefs.avoid_places.filter((n) => n !== name)
        : prefs.avoid_places;
    try {
      const updated = await authApi.updatePreferences({
        favorite_places: favorites,
        avoid_places: avoids,
      });
      setPrefs(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新失败");
    }
  }

  async function clearPrefs() {
    if (!confirm("确定清除全部偏好记忆吗？下次生成将不再参考历史偏好。")) return;
    try {
      await authApi.clearPreferences();
      setPrefs(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "清除失败");
    }
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
      <div className="card overflow-hidden">
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
            className="card p-4 text-center"
          >
            <p className="text-xl">{card.icon}</p>
            <p className="mt-1.5 text-base font-bold text-slate-900">
              {card.value}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Preference memory */}
      <div className="card p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">🧠 偏好记忆</h2>
          {prefs && prefs.generation_count > 0 && (
            <button
              onClick={clearPrefs}
              className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-500 hover:bg-rose-50"
            >
              清除全部
            </button>
          )}
        </div>

        {!prefs || prefs.generation_count === 0 ? (
          <p className="mt-3 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
            还没有偏好数据。生成行程后，系统会慢慢记住你的兴趣、节奏和常去地点，
            下次生成自动参考（可在创建页关闭）。
          </p>
        ) : (
          <>
            <p className="mt-3 rounded-xl bg-teal-50 px-4 py-3 text-sm leading-relaxed text-teal-800">
              {prefs.summary}
            </p>

            {prefs.favorite_places.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-slate-400">常去地点</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {prefs.favorite_places.map((name) => (
                    <span
                      key={name}
                      className="flex items-center gap-1.5 rounded-full bg-teal-50 px-3 py-1.5 text-xs font-medium text-teal-700"
                    >
                      {name}
                      <button
                        onClick={() => removePref(name, "favorite")}
                        className="text-teal-400 hover:text-teal-700"
                        aria-label={`移除 ${name}`}
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {prefs.avoid_places.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-slate-400">不喜欢/删过</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {prefs.avoid_places.map((name) => (
                    <span
                      key={name}
                      className="flex items-center gap-1.5 rounded-full bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-600"
                    >
                      {name}
                      <button
                        onClick={() => removePref(name, "avoid")}
                        className="text-rose-400 hover:text-rose-700"
                        aria-label={`移除 ${name}`}
                      >
                        ✕
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <p className="mt-3 text-[11px] text-slate-400">
              已学习 {prefs.generation_count} 次生成 · 偏好数据仅用于个性化推荐
            </p>
          </>
        )}
      </div>

      {/* Menu */}
      <div className="card overflow-hidden">
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
