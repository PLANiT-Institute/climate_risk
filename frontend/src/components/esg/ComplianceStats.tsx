"use client";

import type { ChecklistItem } from "@/lib/api";

interface Props {
  checklist: ChecklistItem[];
}

export default function ComplianceStats({ checklist }: Props) {
  const total = checklist.length;
  const compliant = checklist.filter((c) => c.status === "compliant").length;
  const partial = checklist.filter((c) => c.status === "partial").length;
  const nonCompliant = checklist.filter((c) => c.status === "non_compliant").length;

  const pctCompliant = Math.round((compliant / total) * 100);
  const pctPartial = Math.round((partial / total) * 100);
  const pctNonCompliant = 100 - pctCompliant - pctPartial;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">준수율 현황</h3>
      <div className="flex h-4 rounded-full overflow-hidden mb-3">
        {pctCompliant > 0 && (
          <div className="bg-green-500 transition-all" style={{ width: `${pctCompliant}%` }} />
        )}
        {pctPartial > 0 && (
          <div className="bg-amber-400 transition-all" style={{ width: `${pctPartial}%` }} />
        )}
        {pctNonCompliant > 0 && (
          <div className="bg-red-400 transition-all" style={{ width: `${pctNonCompliant}%` }} />
        )}
      </div>
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
          <span className="text-slate-600">준수 {compliant}건 ({pctCompliant}%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <span className="text-slate-600">부분 {partial}건 ({pctPartial}%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
          <span className="text-slate-600">미준수 {nonCompliant}건 ({pctNonCompliant}%)</span>
        </div>
      </div>
    </div>
  );
}
