"use client";

import { Building2, MapPin, Factory } from "lucide-react";
import KPICard from "@/components/dashboard/KPICard";
import LoadingCard from "@/components/dashboard/LoadingCard";
import { useFacilities } from "@/hooks/useClimateData";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function CompanyProfilePage() {
  const { data: facilities, isLoading } = useFacilities();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <LoadingCard key={i} rows={1} />)}
        </div>
      </div>
    );
  }

  if (!facilities) return null;

  const totalRevenue = facilities.reduce((s, f) => s + f.annual_revenue, 0);
  const totalAssets = facilities.reduce((s, f) => s + f.assets_value, 0);
  const totalS1 = facilities.reduce((s, f) => s + f.current_emissions_scope1, 0);
  const totalS2 = facilities.reduce((s, f) => s + f.current_emissions_scope2, 0);
  const totalS3 = facilities.reduce((s, f) => s + f.current_emissions_scope3, 0);

  // Group by company
  const companies: Record<string, typeof facilities> = {};
  facilities.forEach((f) => {
    if (!companies[f.company]) companies[f.company] = [];
    companies[f.company].push(f);
  });

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="총 시설 수"
          value={`${facilities.length}개`}
          subtitle={`${Object.keys(companies).length}개 기업`}
          icon={<Factory className="h-5 w-5" />}
        />
        <KPICard
          title="총 매출"
          value={formatCurrency(totalRevenue)}
          icon={<Building2 className="h-5 w-5" />}
        />
        <KPICard
          title="총 자산가치"
          value={formatCurrency(totalAssets)}
        />
        <KPICard
          title="총 배출량 (S1+S2+S3)"
          value={formatNumber(totalS1 + totalS2 + totalS3) + " tCO2e"}
        />
      </div>

      {/* Emissions breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Scope 1 (직접 배출)</h3>
          <p className="text-2xl font-bold text-slate-800">{formatNumber(totalS1)} tCO2e</p>
          <p className="text-xs text-slate-400 mt-1">사업장 직접 배출</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Scope 2 (간접 배출)</h3>
          <p className="text-2xl font-bold text-slate-800">{formatNumber(totalS2)} tCO2e</p>
          <p className="text-xs text-slate-400 mt-1">구매 전력/열 사용</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Scope 3 (가치사슬)</h3>
          <p className="text-2xl font-bold text-slate-800">{formatNumber(totalS3)} tCO2e</p>
          <p className="text-xs text-slate-400 mt-1">공급망 및 제품 사용</p>
        </div>
      </div>

      {/* Company cards */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-700">기업별 시설 현황</h3>
        </div>
        <div className="divide-y divide-slate-50">
          {Object.entries(companies).map(([company, facs]) => {
            const compRevenue = facs.reduce((s, f) => s + f.annual_revenue, 0);
            const compEmissions = facs.reduce((s, f) => s + f.current_emissions_scope1 + f.current_emissions_scope2, 0);
            return (
              <div key={company} className="px-5 py-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-slate-800">{company}</h4>
                    <p className="text-xs text-slate-400">{facs.length}개 시설 &middot; {facs[0].sector}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-mono text-slate-700">{formatCurrency(compRevenue)} 매출</p>
                    <p className="text-xs text-slate-400">{formatNumber(compEmissions)} tCO2e</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {facs.map((f) => (
                    <div key={f.facility_id} className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-700 truncate">{f.name}</p>
                        <p className="text-[10px] text-slate-400">{f.location}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Full facility table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-700">전체 시설 목록</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="text-left py-2.5 px-4 font-medium">시설명</th>
                <th className="text-left py-2.5 px-4 font-medium">기업</th>
                <th className="text-left py-2.5 px-4 font-medium">섹터</th>
                <th className="text-left py-2.5 px-4 font-medium">위치</th>
                <th className="text-right py-2.5 px-4 font-medium">Scope 1</th>
                <th className="text-right py-2.5 px-4 font-medium">Scope 2</th>
                <th className="text-right py-2.5 px-4 font-medium">매출</th>
                <th className="text-right py-2.5 px-4 font-medium">자산가치</th>
              </tr>
            </thead>
            <tbody>
              {facilities.map((f) => (
                <tr key={f.facility_id} className="border-t border-slate-50 hover:bg-slate-50/50">
                  <td className="py-2.5 px-4 font-medium text-slate-800">{f.name}</td>
                  <td className="py-2.5 px-4 text-slate-600">{f.company}</td>
                  <td className="py-2.5 px-4 text-slate-600 capitalize">{f.sector}</td>
                  <td className="py-2.5 px-4 text-slate-500 text-xs">{f.location}</td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-700">{formatNumber(f.current_emissions_scope1)}</td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-700">{formatNumber(f.current_emissions_scope2)}</td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-700">{formatCurrency(f.annual_revenue)}</td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-700">{formatCurrency(f.assets_value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
