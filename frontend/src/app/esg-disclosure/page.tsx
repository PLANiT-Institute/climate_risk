"use client";

import { useState } from "react";
import {
  CheckCircle2,
  AlertCircle,
  XCircle,
  Shield,
  Target,
  Layers,
  BarChart3,
  Calendar,
  ArrowRight,
  Download,
} from "lucide-react";
import LoadingCard from "@/components/dashboard/LoadingCard";
import ESGRadarChart from "@/components/charts/ESGRadarChart";
import ScoreGauge from "@/components/esg/ScoreGauge";
import MaturityGauge from "@/components/esg/MaturityGauge";
import CategoryScoreCard from "@/components/esg/CategoryScoreCard";
import ComplianceStats from "@/components/esg/ComplianceStats";
import MetricsDashboard from "@/components/esg/MetricsDashboard";
import GuidelineMapper from "@/components/esg/GuidelineMapper";
import { useESGAssessment, useESGDisclosure, useESGFrameworks } from "@/hooks/useClimateData";
import { usePartner } from "@/hooks/usePartner";
import { apiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { GapAnalysisItem, RegulatoryDeadline } from "@/lib/api";

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

const SECTION_ICONS: Record<string, React.ReactNode> = {
  governance: <Shield className="h-4 w-4 text-blue-500" />,
  strategy: <Target className="h-4 w-4 text-purple-500" />,
  risk_management: <Layers className="h-4 w-4 text-amber-500" />,
  metrics_and_targets: <BarChart3 className="h-4 w-4 text-green-500" />,
};

const SECTION_NAMES: Record<string, string> = {
  governance: "거버넌스",
  strategy: "전략",
  risk_management: "리스크 관리",
  metrics_and_targets: "지표 및 목표",
};

const FRAMEWORK_DESC: Record<string, string> = {
  tcfd: "기후 관련 재무정보공개 태스크포스 — 거버넌스, 전략, 리스크관리, 지표 및 목표 4대 핵심영역 공시",
  issb: "국제지속가능성기준위원회 (IFRS S2) — 글로벌 기후 공시 표준으로 TCFD 기반 확장",
  kssb: "한국 지속가능성 기준위원회 — ISSB 기반 한국 맥락 적용, K-ETS 연계 및 산업별 추가 공시",
};

function effortLabel(effort: string) {
  if (effort === "low") return { text: "낮음", color: "bg-green-100 text-green-700" };
  if (effort === "medium") return { text: "중간", color: "bg-amber-100 text-amber-700" };
  return { text: "높음", color: "bg-red-100 text-red-700" };
}

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr);
  const now = new Date();
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export default function ESGDisclosurePage() {
  const [framework, setFramework] = useState("tcfd");
  const [isDownloading, setIsDownloading] = useState(false);
  const { partnerId } = usePartner();
  const { data: frameworks } = useESGFrameworks();
  const { data: assessment, isLoading: loadA } = useESGAssessment(framework);
  const { data: disclosure, isLoading: loadD } = useESGDisclosure(framework);

  const handleDownloadReport = async () => {
    setIsDownloading(true);
    try {
      const params = new URLSearchParams({
        framework,
        scenario: "net_zero_2050",
        pricing_regime: "global",
        year: "2030",
      });
      const url = partnerId
        ? apiUrl(`/api/v1/partner/sessions/${partnerId}/esg/reports/disclosure?${params}`)
        : apiUrl(`/api/v1/esg/reports/disclosure?${params}`);
      const res = await fetch(url);
      if (!res.ok) throw new Error("보고서 생성 실패");
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `climate_disclosure_${framework}_net_zero_2050.xlsx`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      console.error(err);
      alert("보고서 다운로드 중 오류가 발생했습니다.");
    } finally {
      setIsDownloading(false);
    }
  };

  if (loadA || loadD) {
    return (
      <div className="space-y-6">
        <div className="flex gap-2">
          {["tcfd", "issb", "kssb"].map((fw) => (
            <button
              key={fw}
              onClick={() => setFramework(fw)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                framework === fw
                  ? "bg-blue-500 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200",
              )}
            >
              {fw.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <LoadingCard key={i} rows={2} />
          ))}
        </div>
      </div>
    );
  }

  if (!assessment) return null;

  const gapAnalysis = (assessment.gap_analysis ?? []) as GapAnalysisItem[];
  const deadlines = (assessment.regulatory_deadlines ?? []) as RegulatoryDeadline[];

  return (
    <div className="space-y-6">
      {/* Framework tabs + description */}
      <div>
        <div className="flex gap-2 mb-2">
          {(
            frameworks ?? [
              { id: "tcfd", name: "TCFD" },
              { id: "issb", name: "ISSB" },
              { id: "kssb", name: "KSSB" },
            ]
          ).map((fw) => (
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
        <p className="text-xs text-slate-400 mb-6">{FRAMEWORK_DESC[framework]}</p>
        <GuidelineMapper framework={framework} />

        <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-blue-900">
              공시 보고서 다운로드
            </h3>
            <p className="text-xs text-blue-600 mt-0.5">
              {framework.toUpperCase()} 프레임워크 기반 Excel 보고서 (8개 시트)
            </p>
          </div>
          <button
            onClick={handleDownloadReport}
            disabled={isDownloading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isDownloading ? (
              <>
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                생성 중...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Excel 다운로드
              </>
            )}
          </button>
        </div>
      </div>

      {/* Score Gauge + Maturity + Compliance Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ScoreGauge score={assessment.overall_score} />
        {assessment.maturity_level ? (
          <MaturityGauge maturity={assessment.maturity_level} />
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm flex items-center justify-center text-sm text-slate-400">
            성숙도 데이터 없음
          </div>
        )}
        <ComplianceStats checklist={assessment.checklist} />
      </div>

      {/* Category Score Cards */}
      <CategoryScoreCard categories={assessment.categories} />

      {/* Radar + Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ESGRadarChart categories={assessment.categories} />

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">공시 체크리스트</h3>
          <div className="space-y-3 max-h-[320px] overflow-y-auto">
            {assessment.checklist.map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0"
              >
                {STATUS_ICON[item.status]}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700">{item.item}</p>
                  {item.recommendation && (
                    <p className="text-xs text-slate-400 mt-0.5">{item.recommendation}</p>
                  )}
                </div>
                <span
                  className={cn(
                    "shrink-0 text-xs px-2 py-0.5 rounded-full",
                    item.status === "compliant"
                      ? "bg-green-100 text-green-700"
                      : item.status === "partial"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700",
                  )}
                >
                  {STATUS_LABEL[item.status]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Metrics Dashboard */}
      {disclosure && <MetricsDashboard disclosure={disclosure} />}

      {/* Gap Analysis */}
      {gapAnalysis.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">갭 분석</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left">
                  <th className="pb-2 text-xs font-semibold text-slate-500">카테고리</th>
                  <th className="pb-2 text-xs font-semibold text-slate-500 text-center">현재</th>
                  <th className="pb-2 text-xs font-semibold text-slate-500 text-center">목표</th>
                  <th className="pb-2 text-xs font-semibold text-slate-500 text-center w-32">
                    진행률
                  </th>
                  <th className="pb-2 text-xs font-semibold text-slate-500 text-center">노력</th>
                  <th className="pb-2 text-xs font-semibold text-slate-500 text-center">
                    우선순위
                  </th>
                  <th className="pb-2 text-xs font-semibold text-slate-500">권고 조치</th>
                </tr>
              </thead>
              <tbody>
                {gapAnalysis
                  .sort((a, b) => b.priority_score - a.priority_score)
                  .map((gap) => {
                    const eff = effortLabel(gap.effort);
                    return (
                      <tr key={gap.category} className="border-b border-slate-50">
                        <td className="py-2.5 font-medium text-slate-700">{gap.category}</td>
                        <td className="py-2.5 text-center text-slate-600">{gap.current_score}</td>
                        <td className="py-2.5 text-center text-slate-600">{gap.target_score}</td>
                        <td className="py-2.5 px-2">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-500 rounded-full"
                                style={{
                                  width: `${(gap.current_score / gap.target_score) * 100}%`,
                                }}
                              />
                            </div>
                            <span className="text-xs text-slate-500 w-6 text-right">
                              {gap.gap}
                            </span>
                          </div>
                        </td>
                        <td className="py-2.5 text-center">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${eff.color}`}
                          >
                            {eff.text}
                          </span>
                        </td>
                        <td className="py-2.5 text-center">
                          <span className="text-xs font-bold text-blue-600">
                            {gap.priority_score.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-2.5 text-xs text-slate-500">
                          {gap.recommended_actions.join(", ")}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Regulatory Deadlines */}
      {deadlines.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">규제 일정</h3>
          <div className="flex flex-col gap-3">
            {deadlines.map((dl, i) => {
              const days = daysUntil(dl.date);
              const isPast = days < 0;
              return (
                <div
                  key={i}
                  className={cn(
                    "flex items-center gap-4 p-3 rounded-lg border",
                    isPast ? "border-slate-200 bg-slate-50" : "border-blue-100 bg-blue-50",
                  )}
                >
                  <Calendar
                    className={cn("h-5 w-5 shrink-0", isPast ? "text-slate-400" : "text-blue-500")}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-700">{dl.name}</p>
                    <p className="text-xs text-slate-400">
                      {dl.description} ({dl.source})
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-slate-500">{dl.date}</p>
                    <p
                      className={cn(
                        "text-xs font-bold",
                        isPast ? "text-slate-400" : days <= 90 ? "text-red-600" : "text-blue-600",
                      )}
                    >
                      {isPast ? "시행 완료" : `D-${days}`}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Disclosure Narrative */}
      {disclosure && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">공시 서술 (초안)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(disclosure.narrative_sections).map(([key, text]) => (
              <div key={key} className="rounded-lg border border-slate-100 p-4">
                <div className="flex items-center gap-2 mb-2">
                  {SECTION_ICONS[key] ?? <ArrowRight className="h-4 w-4 text-slate-400" />}
                  <h4 className="text-sm font-semibold text-slate-700">
                    {SECTION_NAMES[key] ?? key.replace(/_/g, " ")}
                  </h4>
                </div>
                <p className="text-sm text-slate-600 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

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
    </div>
  );
}
