import { Suspense } from "react";
import NewTripForm from "./NewTripForm";

export const metadata = { title: "创建旅行 · TripAI" };

export default function NewTripPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900">创建旅行</h1>
      <p className="mt-1 text-sm text-slate-500">
        填写需求，AI 会在 10 秒内生成每日行程
      </p>
      <div className="mt-6">
        <Suspense fallback={<div className="text-sm text-slate-400">加载中…</div>}>
          <NewTripForm />
        </Suspense>
      </div>
    </div>
  );
}

