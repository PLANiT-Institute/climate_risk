"use client";

import { useState } from "react";
import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import KPICard from "@/components/dashboard/KPICard";
import LoadingCard from "@/components/dashboard/LoadingCard";
import ESGRadarChart from "@/components/charts/ESGRadarChart";
import { useESGAssessment, useESGDisclosure, useESGFrameworks } from "@/hooks/useClimateData";
import { cn } from "@/lib/utils";

const STATUS_ICON: Record<string, React.ReactNode> = {
  compliant: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  partial: <AlertCircle className="h-4 w-4 text-amber-500" />,
  non_compliant: <XCircle className="h-4 w-4 text-red-500" />,
};

const STATUS_LABEL: Record<string, string> = {
  compliant: "준수",
  partial: "부분 준수",
  non_compliant: "미준수",
};

export default function ESGDisclosurePage() {
  const [framework, setFramework] = useState("tcfd");
  const { data: frameworks } = useESGFrameworks();
  const { data: assessment, isLoading: loadA } = useESGAssessment(framework);
  const { data: disclosure, isLoading: loadD } = useESGDisclosure(framework);

  if (loadA || loadD) {
    return (
      <div className="space-y-6">
        <div className="flex gap-2">
          {["tcfd", "issb", "kssb"].map((fw) => (
            <button key={fw} onClick={() => setFramework(fw)}
              className={cn("px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                framework === fw ? "bg-blue-500 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}>
              {fw.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <LoadingCard key={i} rows={2} />)}
        </div>
      </div>
    );
  }

  if (!assessment) return null;

  const compliantCount = assessment.checklist.filter((c) => c.status === "compliant").length;
  const totalItems = assessment.checklist.length;

  return (
    <div className="space-y-6">
      {/* Framework tabs */}
      <div className="flex gap-2">
        {(frameworks ?? [{ id: "tcfd", name: "TCFD" }, { id: "issb", name: "ISSB" }, { id: "kssb", name: "KSSB" }]).map((fw) => (
          <button
            key={fw.id}
            onClick={() => setFramework(fw.id)}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              framework === fw.id
                ? "bg-blue-500 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200",
            )}
          >
            {fw.name}
          </button>
        ))}
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPICard
          title="종합 점수"
          value={`${assessment.overall_score.toFixed(0)}점`}
          subtitle={assessment.compliance_level}
        />
        <KPICard
          title="준수 항목"
          value={`${compliantCount} / ${totalItems}`}
          subtitle={`${((compliantCount / totalItems) * 100).toFixed(0)}% 준수율`}
        />
        <KPICard
          title="프레임워크"
          value={assessment.framework_name}
          subtitle={assessment.framework.toUpperCase()}
        />
      </div>

      {/* Radar + Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ESGRadarChart categories={assessment.categories} />

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">공시 체크리스트</h3>
          <div className="space-y-3 max-h-[320px] overflow-y-auto">
            {assessment.checklist.map((item, i) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
                {STATUS_ICON[item.status]}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700">{item.item}</p>
                  {item.recommendation && (
                    <p className="text-xs text-slate-400 mt-0.5">{item.recommendation}</p>
                  )}
                </div>
                <span className={cn(
                  "shrink-0 text-xs px-2 py-0.5 rounded-full",
                  item.status === "compliant" ? "bg-green-100 text-green-700" :
                  item.status === "partial" ? "bg-amber-100 text-amber-700" :
                  "bg-red-100 text-red-700"
                )}>
                  {STATUS_LABEL[item.status]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {assessment.recommendations.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">개선 권고사항</h3>
          <ul className="space-y-2">
            {assessment.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="mt-0.5 h-5 w-5 shrink-0 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">
                  {i + 1}
                </span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclosure narrative */}
      {disclosure && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">공시 서술 (초안)</h3>
          <div className="space-y-4">
            {Object.entries(disclosure.narrative_sections).map(([key, text]) => (
              <div key={key}>
                <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1">{key.replace(/_/g, " ")}</h4>
                <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
