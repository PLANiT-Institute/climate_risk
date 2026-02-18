"use client";

import type { MaturityLevel } from "@/lib/api";

const LEVELS = [
  { level: 1, name: "인식" },
  { level: 2, name: "기초" },
  { level: 3, name: "개발" },
  { level: 4, name: "관리" },
  { level: 5, name: "선도" },
];

interface Props {
  maturity: MaturityLevel;
}

export default function MaturityGauge({ maturity }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">성숙도 수준</h3>
      <div className="flex items-center gap-1 mb-3">
        {LEVELS.map((lv) => (
          <div key={lv.level} className="flex-1 flex flex-col items-center gap-1">
            <div
              className={`w-full h-3 rounded-full transition-colors ${
                lv.level <= maturity.level
                  ? "bg-blue-500"
                  : "bg-slate-200"
              }`}
            />
            <span className={`text-[10px] ${
              lv.level === maturity.level ? "font-bold text-blue-600" : "text-slate-400"
            }`}>
              {lv.name}
            </span>
          </div>
        ))}
      </div>
      <div className="text-center">
        <span className="text-lg font-bold text-blue-600">Lv.{maturity.level}</span>
        <span className="text-sm text-slate-500 ml-2">{maturity.name}</span>
      </div>
      <p className="text-xs text-slate-400 text-center mt-1">{maturity.description}</p>
    </div>
  );
}
