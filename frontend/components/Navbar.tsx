"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { authApi, clearToken, getToken } from "@/lib/api";
import type { User } from "@/lib/types";

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => clearToken())
      .finally(() => setLoading(false));
  }, [pathname]);

  const linkClass = (path: string) =>
    `rounded-lg px-3 py-2 text-sm font-medium transition ${
      pathname === path
        ? "bg-teal-50 text-teal-700"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 text-lg text-white shadow-sm">
            ✈
          </span>
          <span className="text-lg font-bold tracking-tight text-slate-900">
            TripAI
          </span>
        </Link>

        <nav className="hidden items-center gap-1 sm:flex">
          <Link href="/" className={linkClass("/")}>
            首页
          </Link>
          <Link href="/my-trips" className={linkClass("/my-trips")}>
            我的旅行
          </Link>
          <Link href="/trips/new" className={linkClass("/trips/new")}>
            创建旅行
          </Link>
        </nav>

        <div className="flex items-center gap-2">
          {loading ? null : user ? (
            <>
              <span className="hidden text-sm text-slate-600 sm:inline">
                {user.nickname}
              </span>
              <button
                onClick={() => {
                  clearToken();
                  setUser(null);
                  router.push("/");
                }}
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
              >
                退出
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700"
              >
                注册
              </Link>
            </>
          )}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 sm:hidden"
            aria-label="菜单"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>
      </div>

      {menuOpen && (
        <nav className="border-t border-slate-100 bg-white px-4 py-2 sm:hidden">
          <Link
            href="/"
            className={`block rounded-lg px-3 py-2.5 text-sm font-medium ${pathname === "/" ? "bg-teal-50 text-teal-700" : "text-slate-600"}`}
          >
            首页
          </Link>
          <Link
            href="/my-trips"
            className={`block rounded-lg px-3 py-2.5 text-sm font-medium ${pathname === "/my-trips" ? "bg-teal-50 text-teal-700" : "text-slate-600"}`}
          >
            我的旅行
          </Link>
          <Link
            href="/trips/new"
            className={`block rounded-lg px-3 py-2.5 text-sm font-medium ${pathname === "/trips/new" ? "bg-teal-50 text-teal-700" : "text-slate-600"}`}
          >
            创建旅行
          </Link>
        </nav>
      )}
    </header>
  );
}
