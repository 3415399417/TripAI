"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authApi, setToken } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [nickname, setNickname] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 6) {
      setError("密码至少 6 位");
      return;
    }
    setLoading(true);
    try {
      const res = await authApi.register(email, password, nickname || "旅行者");
      setToken(res.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-gradient-to-br from-teal-50 via-white to-emerald-50 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 text-2xl text-white shadow-lg shadow-teal-600/25">
            ✈
          </span>
          <h1 className="mt-4 text-2xl font-extrabold text-slate-900">创建账号</h1>
          <p className="mt-1 text-sm text-slate-500">注册后即可开始 AI 旅行规划</p>
        </div>

        <div className="rounded-3xl border border-white bg-white/90 p-6 shadow-xl shadow-slate-900/5 backdrop-blur">
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                昵称
              </span>
              <div className="relative">
                <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                  👤
                </span>
                <input
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="旅行者"
                  className="input pl-10"
                />
              </div>
            </label>
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                邮箱
              </span>
              <div className="relative">
                <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                  ✉️
                </span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input pl-10"
                />
              </div>
            </label>
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                密码
              </span>
              <div className="relative">
                <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                  🔒
                </span>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="至少 6 位"
                  className="input pl-10"
                />
              </div>
            </label>

            {error && (
              <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-2xl bg-gradient-to-r from-teal-600 to-emerald-600 py-3.5 font-semibold text-white shadow-lg shadow-teal-600/25 transition hover:opacity-90 disabled:opacity-60"
            >
              {loading ? "注册中…" : "注册"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            已有账号？{" "}
            <Link
              href="/login"
              className="font-semibold text-teal-600 hover:underline"
            >
              去登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
