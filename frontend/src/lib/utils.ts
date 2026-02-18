import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number): string {
  if (Math.abs(n) >= 1e12) return `${(n / 1e12).toFixed(1)}T`;
  if (Math.abs(n) >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toFixed(0);
}

export function formatCurrency(n: number): string {
  const prefix = n < 0 ? "-$" : "$";
  return `${prefix}${formatNumber(Math.abs(n))}`;
}

export function formatPercent(n: number): string {
  return `${n.toFixed(1)}%`;
}

export const RISK_COLORS = {
  High: "#ef4444",
  Medium: "#f59e0b",
  Low: "#22c55e",
} as const;

export const SCENARIO_COLORS: Record<string, string> = {
  net_zero_2050: "#ef4444",
  below_2c: "#f97316",
  delayed_transition: "#eab308",
  current_policies: "#22c55e",
};
