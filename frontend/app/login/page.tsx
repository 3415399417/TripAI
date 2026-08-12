"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authApi, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      setToken(res.access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
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
          <h1 className="mt-4 text-2xl font-extrabold text-slate-900">欢迎回来</h1>
          <p className="mt-1 text-sm text-slate-500">登录后继续你的旅行计划</p>
        </div>

        <div className="rounded-3xl border border-white bg-white/90 p-6 shadow-xl shadow-slate-900/5 backdrop-blur">
          <form onSubmit={handleSubmit} className="space-y-4">
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
                  placeholder="••••••••"
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
              {loading ? "登录中…" : "登录"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            还没有账号？{" "}
            <Link
              href="/register"
              className="font-semibold text-teal-600 hover:underline"
            >
              立即注册
            </Link>
          </p>
          <p className="mt-3 rounded-xl bg-slate-50 px-4 py-2.5 text-center text-xs text-slate-400">
            演示账号：demo@tripai.cn / demo123456
          </p>
        </div>
      </div>
    </div>
  );
}
