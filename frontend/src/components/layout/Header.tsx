"use client";

import { usePathname } from "next/navigation";

const TITLES: Record<string, string> = {
  "/": "개요 대시보드",
  "/transition-risk": "전환 리스크 분석",
  "/physical-risk": "물리적 리스크 분석",
  "/scenario-comparison": "시나리오 비교",
  "/esg-disclosure": "ESG 공시",
  "/company-profile": "기업 프로필",
  "/cashflow-impact": "캐시플로우 영향 분석",
};

export default function Header() {
  const pathname = usePathname();
  const title = TITLES[pathname] ?? "Climate Risk Platform";

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center border-b border-slate-200 bg-white/80 backdrop-blur px-6">
      <h1 className="text-lg font-semibold text-slate-800">{title}</h1>
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
          Sample Data Mode
        </span>
      </div>
    </header>
  );
}
