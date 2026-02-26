"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { usePartner } from "@/hooks/usePartner";
import { apiUrl } from "@/lib/api";
import { Upload, FileJson, Trash2, CheckCircle2, AlertCircle } from "lucide-react";

export default function UploadPage() {
    const router = useRouter();
    const { partnerId, companyName, setPartner } = usePartner();

    const [inputData, setInputData] = useState<string>("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        try {
            setLoading(true);
            setError(null);

            const payload = JSON.parse(inputData);

            const res = await fetch(apiUrl("/api/v1/partner/sessions"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const errDetail = await res.json();
                throw new Error(errDetail.detail || "서버 오류가 발생했습니다.");
            }

            const data = await res.json();
            setPartner(data.partner_id, data.company_name);
            router.push("/");
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message || "올바른 JSON 형식이 아닙니다.");
            } else {
                setError("올바른 JSON 형식이 아닙니다.");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setPartner(null);
        router.refresh();
    };

    return (
        <div className="max-w-3xl space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">커스텀 데이터 등록 (Partner API)</h1>
                <p className="text-slate-500 mt-2">
                    외부 기업의 시설 데이터를 등록하여 동일한 기후리스크 분석을 수행할 수 있습니다.
                    결과는 브라우저에 2시간 동안 임시 저장됩니다.
                </p>
            </div>

            {partnerId ? (
                <div className="rounded-xl border border-green-200 bg-green-50 p-6 flex items-start gap-4">
                    <CheckCircle2 className="h-6 w-6 text-green-500 shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <h3 className="font-semibold text-green-800 text-lg">커스텀 세션 활성화됨</h3>
                        <p className="text-sm text-green-700 mt-1">
                            현재 <strong>{companyName}</strong>의 데이터로 대시보드가 분석되고 있습니다.
                        </p>
                        <div className="mt-4 flex gap-3">
                            <button
                                onClick={() => router.push("/")}
                                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition"
                            >
                                대시보드로 이동
                            </button>
                            <button
                                onClick={handleClear}
                                className="px-4 py-2 bg-white text-red-600 border border-red-200 text-sm font-medium rounded-lg hover:bg-red-50 transition flex items-center gap-2"
                            >
                                <Trash2 className="h-4 w-4" /> 세션 초기화
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                        <FileJson className="h-5 w-5 text-blue-500" />
                        <h3 className="font-semibold text-slate-700">JSON 데이터 입력</h3>
                    </div>

                    <p className="text-sm text-slate-500 mb-4">
                        아래에 Partner API 명세에 맞는 JSON 데이터를 입력하세요.
                    </p>

                    <textarea
                        value={inputData}
                        onChange={(e) => setInputData(e.target.value)}
                        placeholder={'{\n  "company_name": "ABC Corp",\n  "facilities": [\n    {\n      "facility_id": "F001",\n      "name": "ABC 공장",\n      "sector": "steel",\n      "latitude": 37.5,\n      "longitude": 127.0,\n      "current_emissions_scope1": 100000,\n      "current_emissions_scope2": 50000,\n      "annual_revenue": 500000000,\n      "ebitda": 50000000,\n      "assets_value": 1000000000\n    }\n  ]\n}'}
                        className="w-full h-64 p-4 font-mono text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />

                    {error && (
                        <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2 text-red-700 text-sm">
                            <AlertCircle className="h-4 w-4 shrink-0" />
                            {error}
                        </div>
                    )}

                    <div className="mt-6 flex justify-end">
                        <button
                            onClick={handleSubmit}
                            disabled={loading || !inputData.trim()}
                            className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                        >
                            {loading ? (
                                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <Upload className="h-4 w-4" />
                            )}
                            분석 시작하기
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
