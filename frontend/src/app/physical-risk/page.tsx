"use client";

import { useState, useEffect } from "react";
import { Play, MapPin, Database } from "lucide-react";
import KPICard from "@/components/dashboard/KPICard";
import RiskBadge from "@/components/dashboard/RiskBadge";
import LoadingCard from "@/components/dashboard/LoadingCard";
import PhysicalRiskTable from "@/components/tables/PhysicalRiskTable";
import { useFacilities } from "@/hooks/useClimateData";
import { usePartner } from "@/hooks/usePartner";
import { simulatePhysicalRisk } from "@/lib/api";
import type { Facility, PhysicalRiskAssessment } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

const HAZARD_LABELS: Record<string, string> = {
  flood: "홍수",
  typhoon: "태풍",
  heatwave: "폭염",
  drought: "가뭄",
  sea_level_rise: "해수면 상승",
};

const DATA_SOURCE_LABELS: Record<string, string> = {
  open_meteo_api: "실측 데이터 (Open-Meteo API 연동)",
  hardcoded_config: "설정값 기반 (KMA 통계)",
};

export default function PhysicalRiskPage() {
  const { data: baseFacilities, isLoading: isFacLoading } = useFacilities();
  const { partnerId } = usePartner();

  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [useApiData, setUseApiData] = useState(true); // default to real simulation
  const [assessment, setAssessment] = useState<PhysicalRiskAssessment | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simStep, setSimStep] = useState("");

  // Initialize editable facilities when fetched
  useEffect(() => {
    if (baseFacilities && facilities.length === 0) {
      setFacilities(JSON.parse(JSON.stringify(baseFacilities)));
    }
  }, [baseFacilities, facilities.length]);

  const handleRunSimulation = async () => {
    if (facilities.length === 0) return;

    setIsSimulating(true);
    try {
      if (useApiData) setSimStep("Open-Meteo API에서 30개년 기후 데이터 패치 중...");
      else setSimStep("KMA 통계 모델 가동 중...");

      // Artificial delay for UX "deep simulation" feel if using API
      if (useApiData) await new Promise(r => setTimeout(r, 1500));

      setSimStep("재해별 Gumbel 분포 및 EAL 계산 중...");

      const res = await simulatePhysicalRisk(
        {
          scenario: "current_policies",
          year: 2030,
          use_api_data: useApiData,
          facilities: facilities,
        },
        partnerId,
      );

      setAssessment(res);
      setSimStep("");
    } catch (err) {
      console.error(err);
      alert("시뮬레이션 중 오류가 발생했습니다.");
    } finally {
      setIsSimulating(false);
    }
  };

  if (isFacLoading || (facilities.length === 0 && !assessment)) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <LoadingCard key={i} rows={1} />)}
        </div>
      </div>
    );
  }

  // Aggregate hazard counts from assessment
  const hazardCounts: Record<string, { high: number; medium: number; low: number }> = {};
  if (assessment) {
    assessment.facilities.forEach((f) => {
      f.hazards.forEach((h) => {
        if (!hazardCounts[h.hazard_type]) hazardCounts[h.hazard_type] = { high: 0, medium: 0, low: 0 };
        if (h.risk_level === "High") hazardCounts[h.hazard_type].high++;
        else if (h.risk_level === "Medium") hazardCounts[h.hazard_type].medium++;
        else hazardCounts[h.hazard_type].low++;
      });
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-6">

        {/* Left Col: Matrix */}
        <div className="w-full md:w-1/3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm h-fit">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="h-5 w-5 text-indigo-600" />
            <h3 className="font-semibold text-slate-800">Site Configuration Matrix</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            시설 좌표를 수정하여 특정 지역의 실제 기후 영향을 실시간으로 시뮬레이션 하세요.
          </p>

          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
            {facilities.map((fac, idx) => (
              <div key={fac.facility_id} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                <p className="text-sm font-medium text-slate-700">{fac.name}</p>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase font-semibold">Lat</label>
                    <input
                      type="number"
                      value={fac.latitude}
                      onChange={(e) => {
                        const newFacs = [...facilities];
                        newFacs[idx].latitude = parseFloat(e.target.value);
                        setFacilities(newFacs);
                      }}
                      className="w-full text-xs px-2 py-1 rounded border border-slate-300"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase font-semibold">Lon</label>
                    <input
                      type="number"
                      value={fac.longitude}
                      onChange={(e) => {
                        const newFacs = [...facilities];
                        newFacs[idx].longitude = parseFloat(e.target.value);
                        setFacilities(newFacs);
                      }}
                      className="w-full text-xs px-2 py-1 rounded border border-slate-300"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Simulation Config & Results */}
        <div className="w-full md:w-2/3 space-y-6">
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-blue-900 flex items-center gap-2">
                <Database className="h-5 w-5" /> 딥 시뮬레이션 엔진
              </h3>
              <div className="flex items-center gap-2 shrink-0 bg-white rounded-lg border border-blue-200 p-1">
                <button
                  onClick={() => setUseApiData(false)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md ${!useApiData ? "bg-slate-800 text-white" : "text-slate-600 hover:bg-slate-100"}`}
                >
                  기본 통계
                </button>
                <button
                  onClick={() => setUseApiData(true)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md ${useApiData ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
                >
                  Open-Meteo Live API
                </button>
              </div>
            </div>

            <p className="text-sm text-blue-700 mb-5">
              조정된 시설 좌표에서 과거 기상 자료를 다운로드하고 IPCC 방법론에 따라 홍수, 폭염 등의 확률론적 위험을 딥 시뮬레이션합니다.
            </p>

            <button
              onClick={handleRunSimulation}
              disabled={isSimulating}
              className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSimulating ? (
                <>
                  <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {simStep}
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 fill-current" /> Run Deep Simulation
                </>
              )}
            </button>
          </div>

          {!assessment && !isSimulating && (
            <div className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400">
              <Play className="h-12 w-12 mb-4 text-slate-300" />
              <p>시뮬레이션을 실행하여 결과를 확인하세요</p>
            </div>
          )}

          {assessment && !isSimulating && (
            <div className="space-y-6 animate-in fade-in duration-500 slide-in-from-bottom-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <KPICard
                  title="총 연간 예상 손실"
                  value={formatCurrency(assessment.facilities.reduce((sum, f) => sum + f.total_expected_annual_loss, 0))}
                  subtitle={`${assessment.total_facilities}개 시설 합계`}
                  trend="down"
                />
                <KPICard
                  title="고위험 시설"
                  value={`${assessment.overall_risk_summary.High ?? 0}개`}
                  subtitle={`전체 ${assessment.total_facilities}개 중`}
                />
                <KPICard
                  title="데이터 소스"
                  value={assessment.data_source === "open_meteo_api" ? "Open-Meteo" : "KMA Stats"}
                  subtitle={DATA_SOURCE_LABELS[assessment.data_source] ?? assessment.data_source}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {Object.entries(hazardCounts).map(([ht, counts]) => (
                  <div key={ht} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm flex flex-col justify-between">
                    <p className="text-sm font-medium text-slate-700 mb-2">{HAZARD_LABELS[ht] ?? ht}</p>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <RiskBadge level="High" /><span className="text-xs font-semibold">{counts.high}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <RiskBadge level="Medium" /><span className="text-xs text-slate-500">{counts.medium}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <RiskBadge level="Low" /><span className="text-xs text-slate-500">{counts.low}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <PhysicalRiskTable facilities={assessment.facilities} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
