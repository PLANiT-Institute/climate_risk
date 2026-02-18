"use client";

import RiskBadge from "@/components/dashboard/RiskBadge";
import { formatCurrency } from "@/lib/utils";

interface Row {
  facility_id: string;
  facility_name: string;
  sector: string;
  risk_level: string;
  delta_npv: number;
  npv_as_pct_of_assets: number;
}

interface Props {
  facilities: Row[];
}

export default function FacilityRiskTable({ facilities }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-700">시설별 리스크 현황</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="text-left py-2.5 px-4 font-medium">시설</th>
              <th className="text-left py-2.5 px-4 font-medium">섹터</th>
              <th className="text-center py-2.5 px-4 font-medium">리스크</th>
              <th className="text-right py-2.5 px-4 font-medium">NPV 영향</th>
              <th className="text-right py-2.5 px-4 font-medium">자산 대비 %</th>
            </tr>
          </thead>
          <tbody>
            {facilities.map((f) => (
              <tr key={f.facility_id} className="border-t border-slate-50 hover:bg-slate-50/50">
                <td className="py-2.5 px-4">
                  <p className="font-medium text-slate-800">{f.facility_name}</p>
                  <p className="text-xs text-slate-400">{f.facility_id}</p>
                </td>
                <td className="py-2.5 px-4 text-slate-600 capitalize">{f.sector}</td>
                <td className="py-2.5 px-4 text-center">
                  <RiskBadge level={f.risk_level} />
                </td>
                <td className="py-2.5 px-4 text-right font-mono text-slate-700">
                  {formatCurrency(f.delta_npv)}
                </td>
                <td className="py-2.5 px-4 text-right font-mono text-slate-700">
                  {f.npv_as_pct_of_assets.toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
