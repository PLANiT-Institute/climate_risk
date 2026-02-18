import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface Props {
  title: string;
  value: string;
  subtitle?: string;
  icon?: ReactNode;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export default function KPICard({ title, value, subtitle, icon, trend, className }: Props) {
  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white p-5 shadow-sm", className)}>
      <div className="flex items-start justify-between">
        <p className="text-sm text-slate-500">{title}</p>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <p className="mt-2 text-2xl font-bold text-slate-800">{value}</p>
      {subtitle && (
        <p
          className={cn(
            "mt-1 text-xs",
            trend === "down" ? "text-red-500" : trend === "up" ? "text-green-500" : "text-slate-400",
          )}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
}
