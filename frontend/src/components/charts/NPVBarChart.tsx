"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { formatCurrency, SCENARIO_COLORS } from "@/lib/utils";

interface Props {
  data: { scenario: string; scenario_name: string; total_npv: number }[];
}

export default function NPVBarChart({ data }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">시나리오별 전환 비용 NPV</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
          <XAxis
            type="number"
            tickFormatter={(v) => formatCurrency(v)}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="scenario_name"
            width={130}
            tick={{ fontSize: 11 }}
          />
          <Tooltip formatter={(v) => formatCurrency(v as number)} />
          <Bar dataKey="total_npv" radius={[0, 4, 4, 0]}>
            {data.map((d) => (
              <Cell key={d.scenario} fill={SCENARIO_COLORS[d.scenario] ?? "#94a3b8"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
