"use client";

import type { ScheduleItem } from "@/lib/types";

interface PlaceCardProps {
  item: ScheduleItem | null;
  editMode: boolean;
  onMove: (id: number, dir: -1 | 1) => void;
  onRemove: (id: number) => void;
  onUpdate: (id: number, patch: Partial<ScheduleItem>) => void;
}

export default function PlaceCard({
  item,
  editMode,
  onMove,
  onRemove,
  onUpdate,
}: PlaceCardProps) {
  if (!item) {
    return (
      <div className="flex h-full items-center justify-center rounded-2xl border border-slate-200 bg-white p-8">
        <div className="text-center">
          <p className="text-3xl">📍</p>
          <p className="mt-3 text-sm text-slate-500">
            点击左侧行程或地图标记，查看地点详情
          </p>
        </div>
      </div>
    );
  }

  const { place } = item;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold text-slate-900">{place.name}</h3>
          <p className="mt-1 text-sm text-slate-500">
            第 {item.day} 天 · 第 {item.order_index + 1} 站
          </p>
        </div>
        <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">
          {place.category ?? "景点"}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <Info label="建议时间" value={item.recommended_time ?? "—"} />
        <Info
          label="停留时长"
          value={`${item.duration_minutes} 分钟`}
        />
        <Info label="人均花费" value={`约 ¥${item.cost_estimate}`} />
        <Info label="交通方式" value={item.transport ?? "—"} />
        {place.rating ? <Info label="评分" value={`${place.rating} 分`} /> : null}
        {place.address ? (
          <div className="col-span-2">
            <dt className="text-xs font-medium text-slate-400">地址</dt>
            <dd className="mt-0.5 text-slate-700">{place.address}</dd>
          </div>
        ) : null}
      </dl>

      {item.reason ? (
        <div className="mt-4 rounded-xl bg-amber-50 p-3">
          <p className="text-xs font-semibold text-amber-700">推荐理由</p>
          <p className="mt-1 text-sm leading-relaxed text-amber-900">
            {item.reason}
          </p>
        </div>
      ) : null}

      {editMode && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-400">
              建议时间
            </span>
            <input
              value={item.recommended_time ?? ""}
              onChange={(e) => onUpdate(item.id, { recommended_time: e.target.value })}
              placeholder="如 09:00-11:00"
              className="input"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-400">
              停留（分钟）
            </span>
            <input
              type="number"
              min={10}
              value={item.duration_minutes}
              onChange={(e) =>
                onUpdate(item.id, { duration_minutes: Number(e.target.value) })
              }
              className="input"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-400">
              人均花费（元）
            </span>
            <input
              type="number"
              min={0}
              value={item.cost_estimate}
              onChange={(e) =>
                onUpdate(item.id, { cost_estimate: Number(e.target.value) })
              }
              className="input"
            />
          </label>
        </div>
      )}

      {editMode && (
        <div className="mt-5 flex gap-2 border-t border-slate-100 pt-4">
          <button
            onClick={() => onMove(item.id, -1)}
            className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            ↑ 上移
          </button>
          <button
            onClick={() => onMove(item.id, 1)}
            className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            ↓ 下移
          </button>
          <button
            onClick={() => onRemove(item.id)}
            className="flex-1 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50"
          >
            删除
          </button>
        </div>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-400">{label}</dt>
      <dd className="mt-0.5 font-medium text-slate-700">{value}</dd>
    </div>
  );
}
