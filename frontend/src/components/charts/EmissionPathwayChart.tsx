"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatNumber, SCENARIO_COLORS } from "@/lib/utils";

interface Props {
  pathways: Record<string, { year: number; total_emissions: number }[]>;
  scenarioNames?: Record<string, string>;
}

export default function EmissionPathwayChart({ pathways, scenarioNames }: Props) {
  // Merge all scenarios into a single array keyed by year
  const years = new Set<number>();
  for (const pts of Object.values(pathways)) {
    for (const p of pts) years.add(p.year);
  }

  const data = Array.from(years)
    .sort()
    .map((year) => {
      const row: Record<string, number> = { year };
      for (const [sid, pts] of Object.entries(pathways)) {
        const pt = pts.find((p) => p.year === year);
        row[sid] = pt?.total_emissions ?? 0;
      }
      return row;
    });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">배출 경로 (tCO2e)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => formatNumber(v as number)} />
          <Legend />
          {Object.keys(pathways).map((sid) => (
            <Line
              key={sid}
              type="monotone"
              dataKey={sid}
              name={scenarioNames?.[sid] ?? sid}
              stroke={SCENARIO_COLORS[sid] ?? "#94a3b8"}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
