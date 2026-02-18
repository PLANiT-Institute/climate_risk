"use client";

import { useState } from "react";
import KPICard from "@/components/dashboard/KPICard";
import LoadingCard from "@/components/dashboard/LoadingCard";
import NPVBarChart from "@/components/charts/NPVBarChart";
import EmissionPathwayChart from "@/components/charts/EmissionPathwayChart";
import CostTrendChart from "@/components/charts/CostTrendChart";
import RiskHeatMap from "@/components/charts/RiskHeatMap";
import { useTransitionComparison } from "@/hooks/useClimateData";
import { formatCurrency } from "@/lib/utils";

const NAMES: Record<string, string> = {
  net_zero_2050: "Net Zero 2050",
  below_2c: "Below 2°C",
  delayed_transition: "Delayed Transition",
  current_policies: "Current Policies",
};

export default function ScenarioComparisonPage() {
  const [pricingRegime, setPricingRegime] = useState("global");
  const { data, isLoading } = useTransitionComparison(pricingRegime);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <LoadingCard key={i} rows={1} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LoadingCard rows={8} />
          <LoadingCard rows={8} />
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Pricing regime selector */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-500">가격체계:</span>
        <select
          value={pricingRegime}
          onChange={(e) => setPricingRegime(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          <option value="global">Global (USD)</option>
          <option value="kets">K-ETS (KRW)</option>
        </select>
      </div>

      {/* NPV summary per scenario */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {data.npv_comparison.map((s) => (
          <KPICard
            key={s.scenario}
            title={s.scenario_name}
            value={formatCurrency(s.total_npv)}
            subtitle={`평균 리스크: ${s.avg_risk_level}`}
          />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <NPVBarChart data={data.npv_comparison} />
        <RiskHeatMap data={data.risk_distribution} scenarioNames={NAMES} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EmissionPathwayChart pathways={data.emission_pathways} scenarioNames={NAMES} />
        <CostTrendChart trends={data.cost_trends} scenarioNames={NAMES} />
      </div>

      {/* Scenario detail table */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">시나리오 간 리스크 등급 변화</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="text-left py-2.5 px-4 font-medium">시나리오</th>
                <th className="text-center py-2.5 px-4 font-medium">High</th>
                <th className="text-center py-2.5 px-4 font-medium">Medium</th>
                <th className="text-center py-2.5 px-4 font-medium">Low</th>
                <th className="text-right py-2.5 px-4 font-medium">총 NPV</th>
              </tr>
            </thead>
            <tbody>
              {data.npv_comparison.map((s) => {
                const dist = data.risk_distribution[s.scenario];
                return (
                  <tr key={s.scenario} className="border-t border-slate-50">
                    <td className="py-2.5 px-4 font-medium text-slate-700">{s.scenario_name}</td>
                    <td className="py-2.5 px-4 text-center">
                      <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-red-100 text-red-700 text-xs font-bold">
                        {dist.high}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-700 text-xs font-bold">
                        {dist.medium}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-green-100 text-green-700 text-xs font-bold">
                        {dist.low}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-slate-700">
                      {formatCurrency(s.total_npv)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
