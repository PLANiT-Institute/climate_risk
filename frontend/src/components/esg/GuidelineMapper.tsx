import { Shield, Target, Layers, BarChart3, Database, TrendingDown } from "lucide-react";

interface GuidelineMapping {
    framework: string;
}

const MAPPINGS: Record<string, { pillar: string; icon: React.ReactNode; requirement: string; feature: string }[]> = {
    tcfd: [
        {
            pillar: "거버넌스 (Governance)",
            icon: <Shield className="h-5 w-5 text-blue-500" />,
            requirement: "기후 관련 리스크 및 기회에 대한 이사회 관리감독 및 경영진의 역할 공시",
            feature: "ESG 공시 대시보드의 '체크리스트' 기능을 통해 내부 거버넌스 문건 보유 여부 점검 지원"
        },
        {
            pillar: "전략 (Strategy)",
            icon: <Target className="h-5 w-5 text-purple-500" />,
            requirement: "2°C 이하 시나리오 등 다양한 시나리오 기반의 기후 리스크가 비즈니스, 전략 및 재무계획에 미치는 실제 및 잠재적 영향 공시",
            feature: "전환 리스크 모듈 (NGFS Scenarios) 및 탄소세 재무 영향(NPV) 산출 기능으로 S-27 요구사항 직결"
        },
        {
            pillar: "리스크 관리 (Risk Management)",
            icon: <Layers className="h-5 w-5 text-amber-500" />,
            requirement: "기후 리스크를 식별, 평가, 관리하는 프로세스 공시 및 기존 리스크 관리와의 통합 여부",
            feature: "물리적 리스크 딥 시뮬레이션 (RCP 통계 및 Gumbel 분포)을 통한 자산별 식별 및 연간예상손실액(EAL) 정문화 지원"
        },
        {
            pillar: "지표 및 목표 (Metrics & Targets)",
            icon: <BarChart3 className="h-5 w-5 text-green-500" />,
            requirement: "전략 및 리스크 관리 프로세스와 평가에 사용되는 지표 공시 (Scope 1, 2, 3 배출량 포함)",
            feature: "설비별 온실가스 배출량 연동 및 감축목표(Net Zero 2050 등) 달성 궤적 제공"
        }
    ],
    issb: [
        {
            pillar: "거버넌스 (IFRS S2 - 문단 5~7)",
            icon: <Shield className="h-5 w-5 text-blue-500" />,
            requirement: "기후 관련 기회 및 리스크를 모니터링, 관리 및 감독하는 체계",
            feature: "ESG 체크리스트의 이사회 및 경영진 책임 점검을 통해 기초 정보 수집"
        },
        {
            pillar: "재무적 영향 (IFRS S2 - 문단 22)",
            icon: <TrendingDown className="h-5 w-5 text-rose-500" />,
            requirement: "기후 관련 리스크 및 기회가 예상 재무상태, 재무성과 및 현금흐름에 미치는 영향 공시",
            feature: "전환 리스크 모듈의 탄소세 기반 EBITDA 및 자산 NPV 하락률(%) 시뮬레이터가 해당 조항을 직접적으로 충족"
        },
        {
            pillar: "기후 회복력 (IFRS S2 - 문단 27)",
            icon: <Database className="h-5 w-5 text-indigo-500" />,
            requirement: "시나리오 분석을 사용하여 기후 관련 변화에 대한 기업 전략 및 비즈니스 모델의 회복력 평가",
            feature: "물리/전환 NGFS 시나리오 모형화 모듈을 이용한 자산 포트폴리오 회복력 스트레스 테스트 모형"
        },
        {
            pillar: "온실가스 배출량 (IFRS S2 - 문단 29)",
            icon: <BarChart3 className="h-5 w-5 text-green-500" />,
            requirement: "Scope 1, 2, 3 온실가스 배출량 필수 공시",
            feature: "Scope 3 산정 로직(미입력시 0으로 추정) 등 GHG Protocol 기반 기준데이터 업로드"
        }
    ],
    kssb: [
        {
            pillar: "한국 온실가스 배출권거래제 (K-ETS) 연계",
            icon: <TrendingDown className="h-5 w-5 text-rose-500" />,
            requirement: "국내 규제 기준에 따른 스코프별 배출량 및 K-ETS 할당, 부채 예상 공시 (선택/필수 조율 중)",
            feature: "전환 리스크에서 'K-ETS' Pricing Regime 적용 시 부족 배출권 매입 비용(KRW) 자동 시뮬레이션 지원"
        },
        {
            pillar: "시나리오 기반 핵심 재무영향 공시",
            icon: <Target className="h-5 w-5 text-purple-500" />,
            requirement: "전환(정책변경/탄소세) 및 물리(극단적 기상) 요인별 영향 파악 (ISSB IFRS S2와 유사)",
            feature: "Open-Meteo API 실시간 날씨 연동 및 NGFS 정책 시나리오 기반의 재무제표(EBITDA) 삭감 모델제공"
        }
    ]
};

export default function GuidelineMapper({ framework }: GuidelineMapping) {
    const fwKey = framework.toLowerCase();
    const maps = MAPPINGS[fwKey] || MAPPINGS.tcfd;

    return (
        <div className="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-white p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
                <h3 className="text-base font-bold text-indigo-900 border-b-2 border-indigo-200 pb-1">
                    {framework.toUpperCase()} 가이드라인 시스템 맵핑
                </h3>
            </div>
            <p className="text-sm text-slate-600 mb-6 font-medium">
                본 플랫폼의 각종 수리 모형(전환/물리적 리스크) 및 점검 모델이 실제 글로벌 공시 기준({framework.toUpperCase()})의 어느 요구사항을 충족시키는지 설명합니다.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {maps.map((m, i) => (
                    <div key={i} className="flex gap-4 p-4 rounded-lg bg-white border border-indigo-50 hover:shadow-md transition-shadow">
                        <div className="shrink-0 mt-1">{m.icon}</div>
                        <div>
                            <h4 className="text-sm font-bold text-slate-800 mb-1">{m.pillar}</h4>
                            <p className="text-xs text-slate-500 mb-2">{m.requirement}</p>
                            <div className="bg-indigo-50/50 rounded p-2 border border-indigo-100/50 text-xs text-indigo-700">
                                <span className="font-semibold text-indigo-900 mr-1">System Logic:</span>
                                {m.feature}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
