import type { Metadata, Viewport } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import MobileBottomNav from "@/components/MobileBottomNav";
import PwaRegister from "@/components/PwaRegister";

export const metadata: Metadata = {
  title: "TripAI · AI 智能旅行规划",
  description: "输入旅行需求，AI 自动生成行程，地图可视化，一键分享。",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "TripAI",
    statusBarStyle: "default",
  },
  icons: {
    icon: "/icon-192.png",
    apple: "/icon-192.png",
  },
};

// 全站动态渲染，避免页面被网关/浏览器缓存导致用户看到旧版本
export const dynamic = "force-dynamic";

export const viewport: Viewport = {
  themeColor: "#0d9488",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">
        <PwaRegister />
        <Navbar />
        <MobileBottomNav />
        <main className="mx-auto w-full max-w-7xl px-4 py-6 pb-20 sm:px-6 lg:px-8 lg:pb-6">
          {children}
        </main>
      </body>
    </html>
  );
}
