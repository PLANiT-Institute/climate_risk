"use client";

interface Props {
  score: number;
  label?: string;
  size?: number;
}

function scoreColor(score: number) {
  if (score >= 80) return { stroke: "#22c55e", text: "text-green-600", bg: "bg-green-50" };
  if (score >= 65) return { stroke: "#3b82f6", text: "text-blue-600", bg: "bg-blue-50" };
  if (score >= 50) return { stroke: "#f59e0b", text: "text-amber-600", bg: "bg-amber-50" };
  return { stroke: "#ef4444", text: "text-red-600", bg: "bg-red-50" };
}

export default function ScoreGauge({ score, label = "종합 점수", size = 140 }: Props) {
  const r = (size - 16) / 2;
  const circumference = 2 * Math.PI * r;
  const progress = (score / 100) * circumference;
  const color = scoreColor(score);

  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col items-center ${color.bg}`}>
      <h3 className="text-sm font-semibold text-slate-700 mb-3">{label}</h3>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={10}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color.stroke}
            strokeWidth={10}
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${color.text}`}>{score.toFixed(0)}</span>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>
      </div>
    </div>
  );
}
