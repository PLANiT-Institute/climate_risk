"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { formatCurrency } from "@/lib/utils";

interface Props {
  costBreakdown: {
    carbon_cost: number;
    energy_cost_increase: number;
    revenue_impact: number;
    transition_opex: number;
  };
}

const COLORS = ["#ef4444", "#f97316", "#eab308", "#8b5cf6"];

export default function CostWaterfallChart({ costBreakdown }: Props) {
  const items = [
    { name: "탄소 비용 (ETS)", value: costBreakdown.carbon_cost },
    { name: "에너지 비용 증가", value: costBreakdown.energy_cost_increase },
    { name: "매출 영향", value: costBreakdown.revenue_impact },
    { name: "전환 운영비", value: costBreakdown.transition_opex },
  ];

  const total = items.reduce((s, i) => s + i.value, 0);

  const data = [
    ...items,
    { name: "총 비용", value: total },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">비용 구성 (2050년 기준)</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ left: 10, right: 10 }}>
          <XAxis dataKey="name" tick={{ fontSize: 10 }} />
          <YAxis tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => formatCurrency(v as number)} />
          <ReferenceLine y={0} stroke="#e2e8f0" />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={i === data.length - 1 ? "#3b82f6" : COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
