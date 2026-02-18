"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency, SCENARIO_COLORS } from "@/lib/utils";

interface Props {
  trends: Record<string, { year: number; total_cost: number }[]>;
  scenarioNames?: Record<string, string>;
}

export default function CostTrendChart({ trends, scenarioNames }: Props) {
  const years = new Set<number>();
  for (const pts of Object.values(trends)) {
    for (const p of pts) years.add(p.year);
  }

  const data = Array.from(years)
    .sort()
    .map((year) => {
      const row: Record<string, number> = { year };
      for (const [sid, pts] of Object.entries(trends)) {
        const pt = pts.find((p) => p.year === year);
        row[sid] = pt?.total_cost ?? 0;
      }
      return row;
    });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">시나리오별 비용 추이</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => formatCurrency(v as number)} />
          <Legend />
          {Object.keys(trends).map((sid) => (
            <Area
              key={sid}
              type="monotone"
              dataKey={sid}
              name={scenarioNames?.[sid] ?? sid}
              stroke={SCENARIO_COLORS[sid] ?? "#94a3b8"}
              fill={SCENARIO_COLORS[sid] ?? "#94a3b8"}
              fillOpacity={0.1}
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
