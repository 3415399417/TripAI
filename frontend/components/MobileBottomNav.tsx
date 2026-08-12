"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function MobileBottomNav() {
  const pathname = usePathname();

  function isActive(href: string, exact = false): boolean {
    if (exact) return pathname === href || pathname === href + "/";
    return pathname.startsWith(href);
  }

  const tabs = [
    {
      href: "/",
      label: "首页",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75" />
        </svg>
      ),
      exact: true,
    },
    {
      href: "/trips/new",
      label: "创建",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      ),
      highlight: true,
    },
    {
      href: "/me",
      label: "我的",
      icon: (
        <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
      ),
    },
  ];

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 pb-safe backdrop-blur lg:hidden">
      <div className="mx-auto grid max-w-lg grid-cols-3">
        {tabs.map((tab) => {
          const active = tab.exact ? isActive(tab.href, true) : isActive(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`relative flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium transition ${
                active ? "text-teal-600" : "text-slate-400"
              }`}
            >
              {tab.highlight ? (
                <span className="flex h-10 w-10 -mt-3 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 text-white shadow-lg shadow-teal-500/25">
                  {tab.icon}
                </span>
              ) : (
                tab.icon
              )}
              <span className={tab.highlight ? "mt-0.5" : ""}>{tab.label}</span>
              {active && !tab.highlight && (
                <span className="absolute -bottom-0.5 h-0.5 w-6 rounded-full bg-teal-500" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
