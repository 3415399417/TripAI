"use client";

import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, PointerEvent as ReactPointerEvent } from "react";
import { toBlob } from "html-to-image";
import type { Trip } from "@/lib/types";

interface ShareCardModalProps {
  trip: Trip;
  open: boolean;
  onClose: () => void;
}

export default function ShareCardModal({
  trip,
  open,
  onClose,
}: ShareCardModalProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [image, setImage] = useState<string | null>(null);
  const [amount, setAmount] = useState<string>(String(Math.round(trip.budget)));
  const [generated, setGenerated] = useState<string | null>(null);
  const [bgPos, setBgPos] = useState({ x: 0, y: 0 });
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [notice, setNotice] = useState("");
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);
  const imgSizeRef = useRef<{ w: number; h: number } | null>(null);

  useEffect(() => {
    if (open) {
      setImage(null);
      setAmount(String(Math.round(trip.budget)));
      setGenerated(null);
      setBgPos({ x: 0, y: 0 });
      imgSizeRef.current = null;
      setCopied(false);
      setNotice("");
    }
  }, [open]);

  if (!open) return null;

  const [sy, sm, sd] = trip.start_date.slice(0, 10).split("-").map(Number);
  const [ey, em, ed] = trip.end_date.slice(0, 10).split("-").map(Number);
  const dateLabel =
    sy === ey
      ? `${sy}年${sm}月${sd}日 - ${em}月${ed}日`
      : `${sy}年${sm}月${sd}日 - ${ey}年${em}月${ed}日`;

  const dayMap = new Map<number, string[]>();
  trip.schedules.forEach((s) => {
    const arr = dayMap.get(s.day) ?? [];
    arr.push(s.place.name);
    dayMap.set(s.day, arr);
  });
  const totalDays = dayMap.size;
  const totalPlaces = trip.schedules.length;
  const dayRows = [...dayMap.entries()]
    .sort((a, b) => a[0] - b[0])
    .slice(0, 3)
    .map(([day, names]) => ({
      day,
      text:
        names.slice(0, 3).join(" → ") +
        (names.length > 3 ? ` 等${names.length}处` : ""),
    }));
  const hasMoreDays = totalDays > dayRows.length;

  const shownBudget = amount.trim() ? amount : String(Math.round(trip.budget));

  function handleFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setGenerated(null);
    setBgPos({ x: 0, y: 0 });
    imgSizeRef.current = null;
    const reader = new FileReader();
    reader.onload = () => {
      const url = typeof reader.result === "string" ? reader.result : null;
      setImage(url);
      if (url) {
        const img = new Image();
        img.onload = () => {
          imgSizeRef.current = { w: img.naturalWidth, h: img.naturalHeight };
        };
        img.src = url;
      }
    };
    reader.readAsDataURL(file);
  }

  function clamp(v: number, min: number, max: number) {
    return Math.min(max, Math.max(min, v));
  }

  function maxPan() {
    const card = cardRef.current;
    const size = imgSizeRef.current;
    if (!card || !size) return { x: 0, y: 0 };
    const cardW = card.clientWidth;
    const cardH = card.clientHeight;
    const scale = Math.max(cardW / size.w, cardH / size.h);
    return {
      x: Math.max(0, (size.w * scale - cardW) / 2),
      y: Math.max(0, (size.h * scale - cardH) / 2),
    };
  }

  function onPointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    if (!image) return;
    setGenerated(null);
    dragRef.current = {
      pointerId: e.pointerId,
      startX: e.clientX,
      startY: e.clientY,
      originX: bgPos.x,
      originY: bgPos.y,
    };
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    const limit = maxPan();
    setBgPos({
      x: clamp(drag.originX + (e.clientX - drag.startX), -limit.x, limit.x),
      y: clamp(drag.originY + (e.clientY - drag.startY), -limit.y, limit.y),
    });
  }

  function endDrag(e: ReactPointerEvent<HTMLDivElement>) {
    if (dragRef.current?.pointerId === e.pointerId) dragRef.current = null;
  }

  async function generate() {
    if (!cardRef.current || downloading) return;
    setDownloading(true);
    setNotice("");
    try {
      const blob = await toBlob(cardRef.current, {
        pixelRatio: 3,
        cacheBust: true,
      });
      if (!blob) throw new Error("empty blob");
      const url = URL.createObjectURL(blob);
      setGenerated(url);
      const a = document.createElement("a");
      a.href = url;
      a.download = `TripAI-${trip.destination}-旅行卡片.png`;
      a.click();
    } catch {
      setNotice("生成图片失败，请重试");
    } finally {
      setDownloading(false);
    }
  }

  async function copyLink() {
    const url = `${window.location.origin}/trips/${trip.id}/share`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setNotice(`复制失败，请手动复制：${url}`);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="max-h-[92vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-5 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">🎴 分享旅行卡片</h2>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="关闭"
          >
            ✕
          </button>
        </div>

        {/* Card preview */}
        <div className="flex justify-center">
          <div
            ref={cardRef}
            className="relative flex aspect-[3/4] w-full max-w-[340px] select-none flex-col overflow-hidden rounded-3xl text-white shadow-2xl"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={endDrag}
            onPointerCancel={endDrag}
            style={{
              backgroundImage: image ? `url(${image})` : undefined,
              backgroundColor: image ? undefined : "#0f766e",
              backgroundSize: "cover",
              backgroundPosition: image
                ? `calc(50% + ${bgPos.x}px) calc(50% + ${bgPos.y}px)`
                : "center",
              cursor: image ? "grab" : "default",
              touchAction: image ? "none" : undefined,
            }}
          >
            {!image && (
              <>
                <div className="absolute inset-0 bg-gradient-to-br from-teal-500 via-emerald-600 to-sky-700" />
                <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/10" />
                <div className="absolute -bottom-20 -left-14 h-64 w-64 rounded-full bg-white/10" />
                <div className="absolute right-4 top-28 select-none text-8xl opacity-15">
                  ✈️
                </div>
                <div className="absolute bottom-32 left-4 select-none text-7xl opacity-10">
                  🗺️
                </div>
              </>
            )}
            <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/10 to-black/75" />

            <div className="relative flex h-full flex-col p-5">
              {/* top bar */}
              <div className="flex items-center justify-between gap-2">
                <span className="rounded-full bg-white/20 px-3 py-1 text-[11px] font-semibold backdrop-blur">
                  ✈️ TripAI 旅行分享
                </span>
                <span className="rounded-full bg-white/15 px-2.5 py-1 text-[11px] backdrop-blur">
                  {totalDays}天 · {totalPlaces}个地点
                </span>
              </div>

              {/* title & meta — right below the top bar */}
              <div className="mt-6 space-y-2">
                <h3 className="text-[26px] font-extrabold leading-tight drop-shadow-lg">
                  {trip.title}
                </h3>
                <p className="text-sm font-medium text-white/95">
                  📍 {trip.destination} · {dateLabel}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <span className="rounded-full bg-white/20 px-2.5 py-1 text-[11px] backdrop-blur">
                    👥 {trip.travelers} 人
                  </span>
                  <span className="rounded-full bg-white/20 px-2.5 py-1 text-[11px] backdrop-blur">
                    💰 ¥{shownBudget}
                  </span>
                  <span className="rounded-full bg-white/20 px-2.5 py-1 text-[11px] backdrop-blur">
                    🚶 {trip.pace}
                  </span>
                </div>
                {trip.weather && (
                  <p className="text-[11px] text-white/90">
                    🌦 出行天气：{trip.weather}
                  </p>
                )}
              </div>

              {/* itinerary & footer — pinned to the bottom */}
              <div className="mt-auto space-y-2">
                {dayRows.length > 0 && (
                  <div>
                    <p className="mb-1 flex items-center gap-2 text-[10px] font-bold tracking-wider text-white/85">
                      <span className="h-px flex-1 bg-white/25" />
                      行程安排
                      <span className="h-px flex-1 bg-white/25" />
                    </p>
                    <div className="space-y-0.5">
                      {dayRows.map((row) => (
                        <p
                          key={row.day}
                          className="text-[10px] leading-snug text-white/95"
                        >
                          <span className="mr-1 font-bold text-amber-300">
                            D{row.day}
                          </span>
                          {row.text}
                        </p>
                      ))}
                      {hasMoreDays && (
                        <p className="text-[10px] text-white/70">… 共{totalDays}天</p>
                      )}
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between gap-2 border-t border-white/20 pt-2.5">
                  <p className="text-[10px] text-white/70">
                    TripAI · AI 智能旅行规划
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mt-4 space-y-2.5">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5">
            <span className="shrink-0 text-sm text-slate-500">💰 卡片金额</span>
            <input
              type="number"
              inputMode="numeric"
              min={0}
              value={amount}
              onChange={(e) => {
                setAmount(e.target.value);
                setGenerated(null);
              }}
              placeholder="实际花费"
              className="w-full min-w-0 rounded-lg border border-slate-200 px-2 py-1 text-right text-sm font-semibold text-slate-800 focus:border-teal-500 focus:outline-none"
            />
            <span className="shrink-0 text-sm text-slate-400">元</span>
          </div>

          <label className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 py-3 text-sm font-medium text-slate-600 hover:border-teal-400 hover:bg-teal-50/50">
            🖼 {image ? "更换背景图片" : "上传背景图片"}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFile}
            />
          </label>

          {image && (
            <button
              onClick={() => {
                setImage(null);
                setGenerated(null);
                setBgPos({ x: 0, y: 0 });
                imgSizeRef.current = null;
              }}
              className="w-full rounded-xl border border-slate-200 py-2.5 text-sm text-slate-500 hover:bg-slate-50"
            >
              清除图片，使用默认背景
            </button>
          )}

          {image && (
            <div className="flex items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2">
              <p className="text-[11px] text-slate-500">
                🖐 拖动卡片上的图片可调整位置
              </p>
              <button
                onClick={() => {
                  setBgPos({ x: 0, y: 0 });
                  setGenerated(null);
                }}
                className="shrink-0 text-[11px] font-medium text-teal-600 hover:underline"
              >
                重置位置
              </button>
            </div>
          )}

          <button
            onClick={generate}
            disabled={downloading}
            className="w-full rounded-xl bg-teal-600 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700 disabled:opacity-60"
          >
            {downloading ? "生成中…" : "⬇️ 下载卡片图片"}
          </button>

          {generated && (
            <div className="mt-1">
              <img
                src={generated}
                alt="分享旅行卡片"
                className="mx-auto w-full max-w-[340px] rounded-2xl shadow-lg"
              />
              <p className="mt-2 rounded-xl bg-teal-50 px-3 py-2 text-center text-xs text-teal-700">
                ✅ 已生成 · 手机没有自动下载时，<b>长按上方图片</b>即可保存到相册
              </p>
            </div>
          )}

          <button
            onClick={copyLink}
            className="w-full rounded-xl border border-slate-200 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            {copied ? "已复制 ✓" : "🔗 复制分享链接"}
          </button>

          <p className="text-center text-[11px] text-slate-400">
            金额默认显示行程预算，可改成实际花费；图片只在本地合成，不会上传
          </p>

          {notice && (
            <p className="break-all rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-700">
              {notice}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
