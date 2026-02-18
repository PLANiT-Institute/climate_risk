"use client";

import { useState } from "react";
import ScenarioSelector from "@/components/dashboard/ScenarioSelector";
import KPICard from "@/components/dashboard/KPICard";
import LoadingCard from "@/components/dashboard/LoadingCard";
import CostWaterfallChart from "@/components/charts/CostWaterfallChart";
import FacilityRiskTable from "@/components/tables/FacilityRiskTable";
import { useTransitionAnalysis, useTransitionSummary } from "@/hooks/useClimateData";
import { formatCurrency, formatNumber } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function TransitionRiskPage() {
  const [scenario, setScenario] = useState("net_zero_2050");
  const [pricingRegime, setPricingRegime] = useState("global");
  const { data: analysis, isLoading: loadA } = useTransitionAnalysis(scenario, pricingRegime);
  const { data: summary, isLoading: loadS } = useTransitionSummary(scenario, pricingRegime);

  if (loadA || loadS) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <ScenarioSelector value={scenario} onChange={setScenario} />
        </div>
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

  // Aggregate emission pathway across facilities
  const emissionData: Record<number, { scope1: number; scope2: number; total: number }> = {};
  analysis?.facilities.forEach((f) => {
    f.emission_pathway.forEach((pt) => {
      if (!emissionData[pt.year]) emissionData[pt.year] = { scope1: 0, scope2: 0, total: 0 };
      emissionData[pt.year].scope1 += pt.scope1_emissions;
      emissionData[pt.year].scope2 += pt.scope2_emissions;
      emissionData[pt.year].total += pt.total_emissions;
    });
  });
  const pathwayData = Object.entries(emissionData)
    .sort(([a], [b]) => +a - +b)
    .map(([year, v]) => ({ year: +year, ...v }));

  return (
    <div className="space-y-6">
      {/* Scenario selector + Pricing regime */}
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-sm text-slate-500">시나리오:</span>
        <ScenarioSelector value={scenario} onChange={setScenario} />
        <span className="text-sm text-slate-500 ml-2">가격체계:</span>
        <select
          value={pricingRegime}
          onChange={(e) => setPricingRegime(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          <option value="global">Global (USD)</option>
          <option value="kets">K-ETS (KRW)</option>
        </select>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="전환 비용 NPV"
          value={formatCurrency(summary?.total_npv ?? 0)}
          subtitle={`${summary?.scenario_name} ${pricingRegime === "kets" ? "(K-ETS)" : "(Global)"}`}
          trend="down"
        />
        <KPICard
          title="고위험 시설"
          value={`${summary?.high_risk_count ?? 0}개`}
          subtitle={`전체 ${summary?.total_facilities ?? 0}개 중`}
          trend="down"
        />
        <KPICard
          title="중위험 시설"
          value={`${summary?.medium_risk_count ?? 0}개`}
        />
        {pricingRegime === "kets" ? (
          <KPICard
            title="K-ETS 가격체계"
            value="무상할당 적용"
            subtitle="초과 배출분만 과금"
          />
        ) : (
          <KPICard
            title="기준년도 총 배출량"
            value={formatNumber(summary?.total_baseline_emissions ?? 0) + " tCO2e"}
          />
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emission Pathway */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">배출 경로 (연도별)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={pathwayData}>
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => formatNumber(v)} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => formatNumber(v as number)} />
              <Legend />
              <Line type="monotone" dataKey="scope1" name="Scope 1" stroke="#ef4444" strokeWidth={2} />
              <Line type="monotone" dataKey="scope2" name="Scope 2" stroke="#f97316" strokeWidth={2} />
              <Line type="monotone" dataKey="total" name="Total" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Cost waterfall */}
        {summary && <CostWaterfallChart costBreakdown={summary.cost_breakdown} />}
      </div>

      {/* Facility Table */}
      {analysis && (
        <FacilityRiskTable
          facilities={analysis.facilities.map((f) => ({
            facility_id: f.facility_id,
            facility_name: f.facility_name,
            sector: f.sector,
            risk_level: f.risk_level,
            delta_npv: f.delta_npv,
            npv_as_pct_of_assets: f.npv_as_pct_of_assets,
          }))}
        />
      )}
    </div>
  );
}
