"use client";

import { cn } from "@/lib/utils";

interface Props {
  data: Record<string, { high: number; medium: number; low: number }>;
  scenarioNames?: Record<string, string>;
}

function cellColor(val: number, max: number) {
  const ratio = max > 0 ? val / max : 0;
  if (ratio > 0.6) return "bg-red-500 text-white";
  if (ratio > 0.3) return "bg-amber-400 text-slate-800";
  if (ratio > 0) return "bg-green-400 text-slate-800";
  return "bg-slate-100 text-slate-400";
}

export default function RiskHeatMap({ data, scenarioNames }: Props) {
  const scenarios = Object.keys(data);
  const levels = ["high", "medium", "low"] as const;
  const levelLabels = { high: "High", medium: "Medium", low: "Low" };
  const max = Math.max(...scenarios.flatMap((s) => levels.map((l) => data[s][l])));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">시나리오 × 리스크 수준 히트맵</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="text-left py-2 px-3 text-slate-500 font-medium">시나리오</th>
              {levels.map((l) => (
                <th key={l} className="py-2 px-3 text-center text-slate-500 font-medium">
                  {levelLabels[l]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s) => (
              <tr key={s} className="border-t border-slate-100">
                <td className="py-2 px-3 font-medium text-slate-700">
                  {scenarioNames?.[s] ?? s}
                </td>
                {levels.map((l) => (
                  <td key={l} className="py-2 px-3 text-center">
                    <span
                      className={cn(
                        "inline-flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold",
                        cellColor(data[s][l], max),
                      )}
                    >
                      {data[s][l]}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
