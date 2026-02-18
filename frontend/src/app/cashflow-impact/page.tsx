"use client";

import { ArrowRight, TrendingUp, Percent, AlertTriangle } from "lucide-react";

const FLOW_STEPS = [
  { label: "기존 FCF 추정", desc: "과거 재무제표 기반 현금흐름 추정" },
  { label: "전환 리스크 반영", desc: "탄소비용, 에너지비용, 매출영향" },
  { label: "물리적 리스크 반영", desc: "EAL, 자산손상, 복구비용" },
  { label: "할인율 조정", desc: "시나리오별 리스크 프리미엄" },
  { label: "기후조정 NPV", desc: "Climate-adjusted 기업가치" },
];

const OUTPUTS = [
  {
    title: "시나리오별 조정 FCF",
    desc: "탄소비용, EAL, 자산손상을 반영한 시나리오별 현금흐름 변동을 추정합니다.",
    icon: TrendingUp,
    color: "blue",
  },
  {
    title: "Climate-adjusted WACC",
    desc: "시나리오별 리스크 프리미엄을 반영한 기후 리스크 조정 할인율을 산출합니다.",
    icon: Percent,
    color: "orange",
  },
  {
    title: "Climate VaR",
    desc: "최악 시나리오에서의 최대 가치 하락폭을 추정하여 포트폴리오 전체 리스크 규모를 산출합니다.",
    icon: AlertTriangle,
    color: "red",
  },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  blue: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", icon: "text-blue-500" },
  orange: { bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-700", icon: "text-orange-500" },
  red: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", icon: "text-red-500" },
};

export default function CashflowImpactPage() {
  return (
    <div className="space-y-8">
      {/* Banner */}
      <div className="rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
            개발 예정 (2026 H2)
          </span>
        </div>
        <h2 className="text-xl font-bold text-slate-800 mb-1">
          Stage 3: 캐시플로우 영향 분석
        </h2>
        <p className="text-sm text-slate-600">
          Stage 1, 2의 전환 리스크와 물리적 리스크 분석 결과를 통합하여, 기업 현금흐름에 미치는 재무적 영향을 DCF 모델로 정량화합니다.
        </p>
      </div>

      {/* 5-step flow */}
      <div>
        <h3 className="text-base font-semibold text-slate-800 mb-4">분석 방법론 (5단계)</h3>
        <div className="flex items-start gap-2 overflow-x-auto pb-2">
          {FLOW_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-2 shrink-0">
              <div className="w-40 rounded-lg border border-slate-200 bg-white p-3 shadow-sm text-center">
                <div className="text-xs font-bold text-blue-600 mb-1">Step {i + 1}</div>
                <div className="text-sm font-semibold text-slate-800 mb-1">{step.label}</div>
                <div className="text-[11px] text-slate-500">{step.desc}</div>
              </div>
              {i < FLOW_STEPS.length - 1 && (
                <ArrowRight className="h-4 w-4 text-slate-400 shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Output cards */}
      <div>
        <h3 className="text-base font-semibold text-slate-800 mb-4">주요 산출물</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {OUTPUTS.map(({ title, desc, icon: Icon, color }) => {
            const c = COLOR_MAP[color];
            return (
              <div
                key={title}
                className={`rounded-xl border ${c.border} ${c.bg} p-5 shadow-sm`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Icon className={`h-5 w-5 ${c.icon}`} />
                  <h4 className={`text-sm font-bold ${c.text}`}>{title}</h4>
                </div>
                <p className="text-sm text-slate-600">{desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Integration diagram */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-base font-semibold text-slate-800 mb-4">Stage 1+2 결과 통합</h3>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <div className="rounded-lg bg-blue-50 border border-blue-200 px-5 py-3 text-center">
            <div className="text-xs text-blue-500 font-medium mb-1">Stage 1</div>
            <div className="text-sm font-semibold text-blue-700">전환 리스크</div>
            <div className="text-[11px] text-slate-500 mt-1">탄소비용, NPV 영향</div>
          </div>
          <span className="text-2xl text-slate-300 font-light">+</span>
          <div className="rounded-lg bg-orange-50 border border-orange-200 px-5 py-3 text-center">
            <div className="text-xs text-orange-500 font-medium mb-1">Stage 1</div>
            <div className="text-sm font-semibold text-orange-700">물리적 리스크</div>
            <div className="text-[11px] text-slate-500 mt-1">EAL, 자산손상</div>
          </div>
          <span className="text-2xl text-slate-300 font-light">+</span>
          <div className="rounded-lg bg-purple-50 border border-purple-200 px-5 py-3 text-center">
            <div className="text-xs text-purple-500 font-medium mb-1">Stage 2</div>
            <div className="text-sm font-semibold text-purple-700">시나리오 분석</div>
            <div className="text-[11px] text-slate-500 mt-1">4개 NGFS 경로</div>
          </div>
          <ArrowRight className="h-5 w-5 text-slate-400" />
          <div className="rounded-lg bg-green-50 border border-green-200 px-5 py-3 text-center">
            <div className="text-xs text-green-500 font-medium mb-1">Stage 3</div>
            <div className="text-sm font-semibold text-green-700">캐시플로우 모델</div>
            <div className="text-[11px] text-slate-500 mt-1">DCF 기반 재무영향</div>
          </div>
        </div>
      </div>
    </div>
  );
}
