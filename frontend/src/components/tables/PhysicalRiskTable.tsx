"use client";

import RiskBadge from "@/components/dashboard/RiskBadge";
import { formatCurrency } from "@/lib/utils";
import type { FacilityPhysicalRisk } from "@/lib/api";

interface Props {
  facilities: FacilityPhysicalRisk[];
}

export default function PhysicalRiskTable({ facilities }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-700">시설별 물리적 리스크</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="text-left py-2.5 px-4 font-medium">시설</th>
              <th className="text-left py-2.5 px-4 font-medium">위치</th>
              <th className="text-center py-2.5 px-4 font-medium">종합 리스크</th>
              <th className="text-right py-2.5 px-4 font-medium">연간 예상 손실</th>
              <th className="text-center py-2.5 px-4 font-medium">주요 재해</th>
            </tr>
          </thead>
          <tbody>
            {facilities.map((f) => {
              const topHazard = f.hazards.reduce((a, b) =>
                b.potential_loss > a.potential_loss ? b : a,
              );
              return (
                <tr key={f.facility_id} className="border-t border-slate-50 hover:bg-slate-50/50">
                  <td className="py-2.5 px-4">
                    <p className="font-medium text-slate-800">{f.facility_name}</p>
                    <p className="text-xs text-slate-400">{f.facility_id}</p>
                  </td>
                  <td className="py-2.5 px-4 text-slate-600">{f.location}</td>
                  <td className="py-2.5 px-4 text-center">
                    <RiskBadge level={f.overall_risk_level} />
                  </td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-700">
                    {formatCurrency(f.total_expected_annual_loss)}
                  </td>
                  <td className="py-2.5 px-4 text-center text-xs text-slate-600">
                    {topHazard.hazard_type}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
