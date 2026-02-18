"use client";

import type { FrameworkScore } from "@/lib/api";

function barColor(score: number) {
  if (score >= 80) return "bg-green-500";
  if (score >= 65) return "bg-blue-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

function badgeStyle(status: string) {
  if (status === "우수") return "bg-green-100 text-green-700";
  if (status === "양호") return "bg-blue-100 text-blue-700";
  if (status === "보통") return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
}

interface Props {
  categories: FrameworkScore[];
}

export default function CategoryScoreCard({ categories }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">카테고리별 점수</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {categories.map((cat) => (
          <div key={cat.category} className="rounded-lg border border-slate-100 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-700">{cat.category}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${badgeStyle(cat.status)}`}>
                {cat.status}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barColor(cat.score)}`}
                  style={{ width: `${(cat.score / cat.max_score) * 100}%` }}
                />
              </div>
              <span className="text-sm font-bold text-slate-700 w-8 text-right">{cat.score}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
