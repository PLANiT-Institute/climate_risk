"use client";

import Link from "next/link";
import { Activity, Factory, TrendingDown, Shield, ArrowRight } from "lucide-react";
import KPICard from "@/components/dashboard/KPICard";
import NPVBarChart from "@/components/charts/NPVBarChart";
import RiskHeatMap from "@/components/charts/RiskHeatMap";
import EmissionPathwayChart from "@/components/charts/EmissionPathwayChart";
import LoadingCard from "@/components/dashboard/LoadingCard";
import { useTransitionComparison, useFacilities, useESGAssessment } from "@/hooks/useClimateData";
import { formatCurrency, formatNumber } from "@/lib/utils";

const SCENARIO_NAMES: Record<string, string> = {
  net_zero_2050: "Net Zero 2050",
  below_2c: "Below 2°C",
  delayed_transition: "Delayed Transition",
  current_policies: "Current Policies",
};

export default function DashboardPage() {
  const { data: comparison, isLoading: loadComp } = useTransitionComparison();
  const { data: facilities, isLoading: loadFac } = useFacilities();
  const { data: esg, isLoading: loadESG } = useESGAssessment("tcfd");

  const isLoading = loadComp || loadFac || loadESG;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <LoadingCard key={i} rows={1} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LoadingCard rows={8} />
          <LoadingCard rows={8} />
        </div>
      </div>
    );
  }

  const totalEmissions = facilities
    ? facilities.reduce((s, f) => s + f.current_emissions_scope1 + f.current_emissions_scope2, 0)
    : 0;

  const nzNpv = comparison?.npv_comparison.find((c) => c.scenario === "net_zero_2050")?.total_npv ?? 0;

  const highRisk = comparison
    ? Object.values(comparison.risk_distribution).reduce((s, d) => s + d.high, 0) / Object.keys(comparison.risk_distribution).length
    : 0;

  const stages = [
    {
      stage: "Stage 1",
      title: "기초 분석",
      desc: "전환+물리적 리스크 개요",
      href: "/transition-risk",
      color: "blue" as const,
      badge: "제공 중",
    },
    {
      stage: "Stage 2",
      title: "심층 시나리오",
      desc: "NGFS 4개 시나리오 비교",
      href: "/scenario-comparison",
      color: "orange" as const,
      badge: "제공 중",
    },
    {
      stage: "Stage 3",
      title: "캐시플로우",
      desc: "DCF 기반 재무영향",
      href: "/cashflow-impact",
      color: "green" as const,
      badge: "개발 예정",
    },
  ];

  const stageColors = {
    blue: { border: "border-blue-200", bg: "bg-blue-50", accent: "text-blue-600", badge: "bg-blue-100 text-blue-700" },
    orange: { border: "border-orange-200", bg: "bg-orange-50", accent: "text-orange-600", badge: "bg-orange-100 text-orange-700" },
    green: { border: "border-green-200", bg: "bg-green-50", accent: "text-green-600", badge: "bg-amber-100 text-amber-700" },
  };

  return (
    <div className="space-y-6">
      {/* 3-Stage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stages.map((s) => {
          const c = stageColors[s.color];
          return (
            <Link
              key={s.stage}
              href={s.href}
              className={`group rounded-xl border ${c.border} ${c.bg} p-4 shadow-sm hover:shadow-md transition-shadow`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs font-bold ${c.accent}`}>{s.stage}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${c.badge}`}>
                  {s.badge}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-800 mb-1">{s.title}</h3>
              <p className="text-xs text-slate-500 mb-2">{s.desc}</p>
              <div className="flex items-center gap-1 text-xs font-medium text-slate-400 group-hover:text-slate-600 transition-colors">
                자세히 보기 <ArrowRight className="h-3 w-3" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="총 배출량 (Scope 1+2)"
          value={formatNumber(totalEmissions) + " tCO2e"}
          subtitle={`${facilities?.length ?? 0}개 시설 합계`}
          icon={<Activity className="h-5 w-5" />}
        />
        <KPICard
          title="전환비용 NPV (Net Zero)"
          value={formatCurrency(nzNpv)}
          subtitle="Net Zero 2050 시나리오"
          trend="down"
          icon={<TrendingDown className="h-5 w-5" />}
        />
        <KPICard
          title="ESG 준비도"
          value={`${esg?.overall_score.toFixed(0) ?? "-"}점`}
          subtitle={esg?.compliance_level ?? ""}
          icon={<Shield className="h-5 w-5" />}
        />
        <KPICard
          title="고위험 시설 (평균)"
          value={`${Math.round(highRisk)}개`}
          subtitle="시나리오 평균 기준"
          trend="down"
          icon={<Factory className="h-5 w-5" />}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {comparison && (
          <NPVBarChart data={comparison.npv_comparison} />
        )}
        {comparison && (
          <RiskHeatMap data={comparison.risk_distribution} scenarioNames={SCENARIO_NAMES} />
        )}
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {comparison && (
          <EmissionPathwayChart pathways={comparison.emission_pathways} scenarioNames={SCENARIO_NAMES} />
        )}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">섹터별 배출 현황</h3>
          <div className="space-y-3">
            {facilities &&
              Object.entries(
                facilities.reduce<Record<string, number>>((acc, f) => {
                  acc[f.sector] = (acc[f.sector] ?? 0) + f.current_emissions_scope1 + f.current_emissions_scope2;
                  return acc;
                }, {}),
              )
                .sort(([, a], [, b]) => b - a)
                .map(([sector, emissions]) => (
                  <div key={sector} className="flex items-center gap-3">
                    <span className="w-24 text-xs text-slate-500 capitalize">{sector}</span>
                    <div className="flex-1 h-5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(emissions / totalEmissions) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono text-slate-600 w-20 text-right">
                      {formatNumber(emissions)}
                    </span>
                  </div>
                ))}
          </div>
        </div>
      </div>
    </div>
  );
}
