"use client";

import type { ESGDisclosureData } from "@/lib/api";

function formatNumber(n: number): string {
  if (Math.abs(n) >= 1e12) return `${(n / 1e12).toFixed(1)}조`;
  if (Math.abs(n) >= 1e8) return `${(n / 1e8).toFixed(1)}억`;
  if (Math.abs(n) >= 1e4) return `${(n / 1e4).toFixed(0)}만`;
  return n.toLocaleString();
}

interface Props {
  disclosure: ESGDisclosureData;
}

export default function MetricsDashboard({ disclosure }: Props) {
  const emissions = disclosure.metrics?.emissions as Record<string, number> | undefined;
  const financial = disclosure.metrics?.financial_impact as Record<string, number> | undefined;
  const targets = disclosure.metrics?.targets as Record<string, number | boolean> | undefined;

  if (!emissions && !financial && !targets) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">주요 지표 대시보드</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {emissions && (
          <div className="rounded-lg bg-slate-50 p-4">
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-3">배출량</h4>
            <div className="space-y-2">
              <MetricRow label="Scope 1" value={`${formatNumber(emissions.scope1_tco2e)} tCO2e`} />
              <MetricRow label="Scope 2" value={`${formatNumber(emissions.scope2_tco2e)} tCO2e`} />
              <MetricRow label="Scope 3" value={`${formatNumber(emissions.scope3_tco2e)} tCO2e`} />
              <div className="border-t border-slate-200 pt-1.5">
                <MetricRow label="합계" value={`${formatNumber(emissions.total_tco2e)} tCO2e`} bold />
              </div>
              <MetricRow label="원단위" value={`${emissions.intensity_tco2e_per_revenue} tCO2e/억원`} />
            </div>
          </div>
        )}

        {financial && (
          <div className="rounded-lg bg-slate-50 p-4">
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-3">재무 영향</h4>
            <div className="space-y-2">
              <MetricRow
                label="전환 리스크 NPV"
                value={`${formatNumber(financial.transition_risk_npv_net_zero)}원`}
                negative
              />
              <MetricRow label="리스크 시설" value={`${financial.total_facilities}개`} />
              <MetricRow label="위험 자산" value={`${formatNumber(financial.total_assets_at_risk)}원`} />
            </div>
          </div>
        )}

        {targets && (
          <div className="rounded-lg bg-slate-50 p-4">
            <h4 className="text-xs font-semibold text-slate-500 uppercase mb-3">감축 목표</h4>
            <div className="space-y-2">
              <MetricRow label="기준연도" value={String(targets.base_year)} />
              <MetricRow label="목표연도" value={String(targets.target_year)} />
              <MetricRow label="감축 목표" value={`${targets.reduction_target_pct}%`} bold />
              <MetricRow
                label="SBTi 인증"
                value={targets.science_based ? "Yes" : "No"}
                badge={targets.science_based ? "green" : "red"}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  bold,
  negative,
  badge,
}: {
  label: string;
  value: string;
  bold?: boolean;
  negative?: boolean;
  badge?: "green" | "red";
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-500">{label}</span>
      {badge ? (
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          badge === "green" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
        }`}>
          {value}
        </span>
      ) : (
        <span className={`text-xs ${bold ? "font-bold text-slate-800" : "text-slate-700"} ${negative ? "text-red-600" : ""}`}>
          {value}
        </span>
      )}
    </div>
  );
}
