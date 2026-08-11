"use client";

import { useEffect, useRef, useState } from "react";

const AMAP_JS_KEY = process.env.NEXT_PUBLIC_AMAP_JS_KEY ?? "";
const TILE_TIMEOUT_MS = 10_000; // 10s 内瓦片未加载完认为失败

export interface MapPlace {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  day: number;
  order_index: number;
}

interface MapViewProps {
  places: MapPlace[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  focusId?: number | null;
  focusNonce?: number;
  className?: string;
}

type MapStatus = "loading" | "ready" | "missing-key" | "tiles-failed" | "error";

export default function MapView({
  places,
  selectedId,
  onSelect,
  focusId = null,
  focusNonce = 0,
  className = "",
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const polylineRef = useRef<any>(null);
  const lastFitKey = useRef<string>("");
  const tileTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [status, setStatus] = useState<MapStatus>(
    AMAP_JS_KEY ? "loading" : "missing-key"
  );

  // Load the map once
  useEffect(() => {
    if (!AMAP_JS_KEY || !containerRef.current || mapRef.current) return;
    let disposed = false;

    // Load the AMap loader dynamically so it never executes during SSR
    // (the package references `window` at module evaluation time).
    (async () => {
      const { default: AMapLoader } = await import("@amap/amap-jsapi-loader");
      const AMap = await AMapLoader.load({
        key: AMAP_JS_KEY,
        version: "2.0",
      });
      if (disposed || !containerRef.current) return;
      mapRef.current = new AMap.Map(containerRef.current, {
        zoom: 11,
        resizeEnable: true,
      });

      // Detect tile load success/failure
      let completeFired = false;
      if (typeof mapRef.current.on === "function") {
        mapRef.current.on("complete", () => {
          completeFired = true;
          if (tileTimer.current) {
            clearTimeout(tileTimer.current);
            tileTimer.current = null;
          }
          if (!disposed) setStatus("ready");
        });
      }

      // Fallback: if tiles haven't arrived within timeout, flag as tiles-failed
      tileTimer.current = setTimeout(() => {
        if (!completeFired && !disposed) {
          setStatus("tiles-failed");
        }
      }, TILE_TIMEOUT_MS);

      if (!completeFired) {
        setStatus("ready"); // markers work immediately, tiles may still be loading
      }
    })().catch(() => {
      if (!disposed) setStatus("error");
    });

    return () => {
      disposed = true;
      if (tileTimer.current) {
        clearTimeout(tileTimer.current);
        tileTimer.current = null;
      }
      mapRef.current?.destroy();
      mapRef.current = null;
    };
  }, []);

  // Render markers / polyline whenever places or selection change
  useEffect(() => {
    const map = mapRef.current;
    if (!map || (status !== "ready" && status !== "tiles-failed")) return;

    markersRef.current.forEach((m) => map.remove(m));
    markersRef.current = [];
    if (polylineRef.current) {
      map.remove(polylineRef.current);
      polylineRef.current = null;
    }

    const AMap = (window as any).AMap;
    if (!AMap || places.length === 0) return;

    places.forEach((p, index) => {
      const content = document.createElement("div");
      content.className =
        "tripai-marker" + (selectedId === p.id ? " selected" : "");
      content.innerHTML = `<span>${index + 1}</span>`;
      content.onclick = () => onSelect(p.id);
      const marker = new AMap.Marker({
        position: [p.longitude, p.latitude],
        content,
        offset: new AMap.Pixel(-16, -40),
        title: p.name,
      });
      map.add(marker);
      markersRef.current.push(marker);
    });

    if (places.length >= 2) {
      polylineRef.current = new AMap.Polyline({
        path: places.map((p) => [p.longitude, p.latitude]),
        strokeColor: "#0d9488",
        strokeWeight: 4,
        strokeOpacity: 0.85,
        lineJoin: "round",
        lineCap: "round",
        showDir: true,
      });
      map.add(polylineRef.current);
    }

    const fitKey = places.map((p) => `${p.id}`).join(",");
    if (fitKey !== lastFitKey.current && places.length > 0) {
      lastFitKey.current = fitKey;
      map.setFitView(markersRef.current, false, [40, 40, 40, 40]);
    }
  }, [places, selectedId, status, onSelect]);

  // Zoom to a specific place when requested from the detail view
  useEffect(() => {
    const map = mapRef.current;
    if (!map || (status !== "ready" && status !== "tiles-failed")) return;
    if (focusId == null) return;
    const target = places.find((p) => p.id === focusId);
    if (!target) return;
    map.setZoomAndCenter(15, [target.longitude, target.latitude]);
  }, [focusId, focusNonce, places, status]);

  if (status === "missing-key") {
    return (
      <div
        className={`flex items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-100 ${className}`}
      >
        <div className="max-w-sm px-6 text-center">
          <p className="text-3xl">🗺️</p>
          <p className="mt-3 text-sm font-semibold text-slate-700">
            未配置高德地图 Key
          </p>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            在{" "}
            <a
              className="font-medium text-teal-600 underline"
              href="https://console.amap.com/dev/key/app"
              target="_blank"
              rel="noreferrer"
            >
              高德开放平台
            </a>{" "}
            申请「Web 端(JS API)」Key 后，填入前端的
            NEXT_PUBLIC_AMAP_JS_KEY 即可显示地图。
          </p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div
        className={`flex items-center justify-center rounded-2xl bg-rose-50 ${className}`}
      >
        <p className="px-6 text-center text-sm text-rose-600">
          地图加载失败，请检查 Key 是否正确。
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className={`rounded-2xl overflow-hidden bg-slate-100 ${className}`}
      >
        {status === "loading" && (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            地图加载中…
          </div>
        )}
      </div>

      {/* Tile load failure warning */}
      {status === "tiles-failed" && (
        <div className="absolute inset-x-0 top-2 mx-auto w-fit rounded-xl border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 shadow-sm">
          ⚠️ 地图瓦片加载失败，请尝试切换网络或刷新页面
        </div>
      )}
    </div>
  );
}
