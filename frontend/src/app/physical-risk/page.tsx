"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import KPICard from "@/components/dashboard/KPICard";
import RiskBadge from "@/components/dashboard/RiskBadge";
import LoadingCard from "@/components/dashboard/LoadingCard";
import PhysicalRiskTable from "@/components/tables/PhysicalRiskTable";
import { usePhysicalRisk } from "@/hooks/useClimateData";
import { formatCurrency } from "@/lib/utils";

const HAZARD_LABELS: Record<string, string> = {
  flood: "홍수",
  typhoon: "태풍",
  heatwave: "폭염",
  drought: "가뭄",
  sea_level_rise: "해수면 상승",
};

const DATA_SOURCE_LABELS: Record<string, string> = {
  open_meteo_api: "실측 데이터 (Open-Meteo)",
  hardcoded_config: "설정값 기반 (KMA 통계)",
};

export default function PhysicalRiskPage() {
  const [useApiData, setUseApiData] = useState(false);
  const { data, isLoading } = usePhysicalRisk(useApiData);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <LoadingCard key={i} rows={1} />)}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const totalEAL = data.facilities.reduce((s, f) => s + f.total_expected_annual_loss, 0);

  // Aggregate hazard counts
  const hazardCounts: Record<string, { high: number; medium: number; low: number }> = {};
  data.facilities.forEach((f) => {
    f.hazards.forEach((h) => {
      if (!hazardCounts[h.hazard_type]) hazardCounts[h.hazard_type] = { high: 0, medium: 0, low: 0 };
      if (h.risk_level === "High") hazardCounts[h.hazard_type].high++;
      else if (h.risk_level === "Medium") hazardCounts[h.hazard_type].medium++;
      else hazardCounts[h.hazard_type].low++;
    });
  });

  return (
    <div className="space-y-6">
      {/* Model info banner + data source toggle */}
      <div className="flex items-center justify-between gap-3 rounded-xl bg-blue-50 border border-blue-200 p-4">
        <div className="flex items-center gap-3">
          <Info className="h-5 w-5 text-blue-500 shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800">Analytical v1 모델</p>
            <p className="text-xs text-blue-600 mt-0.5">
              KMA 30년 통계 + IPCC AR6 기반 물리적 리스크 평가 (Gumbel/Poisson)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-500">데이터 소스:</span>
          <button
            onClick={() => setUseApiData(false)}
            className={`px-2.5 py-1 text-xs rounded-l-lg border ${!useApiData ? "bg-blue-500 text-white border-blue-500" : "bg-white text-slate-600 border-slate-200"}`}
          >
            설정값 기반
          </button>
          <button
            onClick={() => setUseApiData(true)}
            className={`px-2.5 py-1 text-xs rounded-r-lg border -ml-px ${useApiData ? "bg-blue-500 text-white border-blue-500" : "bg-white text-slate-600 border-slate-200"}`}
          >
            Open-Meteo API
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPICard
          title="총 연간 예상 손실"
          value={formatCurrency(totalEAL)}
          subtitle={`${data.total_facilities}개 시설 합계`}
          trend="down"
        />
        <KPICard
          title="고위험 시설"
          value={`${data.overall_risk_summary.High ?? 0}개`}
          subtitle={`전체 ${data.total_facilities}개 중`}
        />
        <KPICard
          title="분석 모델"
          value={data.model_status === "analytical_v1" ? "Analytical v1" : data.model_status}
          subtitle={DATA_SOURCE_LABELS[data.data_source] ?? data.data_source ?? "물리적 리스크 모델"}
        />
      </div>

      {/* Hazard type cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {Object.entries(hazardCounts).map(([ht, counts]) => (
          <div key={ht} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm font-medium text-slate-700 mb-3">{HAZARD_LABELS[ht] ?? ht}</p>
            <div className="flex items-center gap-2">
              <RiskBadge level="High" />
              <span className="text-xs text-slate-500">{counts.high}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <RiskBadge level="Medium" />
              <span className="text-xs text-slate-500">{counts.medium}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <RiskBadge level="Low" />
              <span className="text-xs text-slate-500">{counts.low}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Table */}
      <PhysicalRiskTable facilities={data.facilities} />
    </div>
  );
}
