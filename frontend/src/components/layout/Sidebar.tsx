"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ArrowRightLeft,
  CloudRain,
  GitCompare,
  FileCheck,
  Building2,
  Banknote,
  FileUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { usePartner } from "@/hooks/usePartner";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  badge?: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "",
    items: [
      { href: "/", label: "대시보드", icon: LayoutDashboard },
      { href: "/upload", label: "데이터 등록", icon: FileUp, badge: "Custom" },
    ],
  },
  {
    label: "Stage 1 · 기초 분석",
    items: [
      { href: "/transition-risk", label: "전환 리스크", icon: ArrowRightLeft },
      { href: "/physical-risk", label: "물리적 리스크", icon: CloudRain },
    ],
  },
  {
    label: "Stage 2 · 심층 시나리오",
    items: [
      { href: "/scenario-comparison", label: "시나리오 비교", icon: GitCompare },
      { href: "/esg-disclosure", label: "ESG 공시", icon: FileCheck },
    ],
  },
  {
    label: "Stage 3 · 캐시플로우",
    items: [
      { href: "/cashflow-impact", label: "캐시플로우 영향", icon: Banknote, badge: "예정" },
    ],
  },
  {
    label: "",
    items: [{ href: "/company-profile", label: "기업 프로필", icon: Building2 }],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { partnerId, companyName } = usePartner();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-slate-800 text-slate-200">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 px-5 border-b border-slate-700">
        <div className="h-8 w-8 rounded-lg bg-blue-500 flex items-center justify-center text-white font-bold text-sm">
          CR
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Climate Risk</p>
          <p className="text-[10px] text-slate-400">Platform v1.0</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi}>
            {group.label && (
              <p className="text-[10px] uppercase tracking-wider text-slate-500 px-3 pt-4 pb-1">
                {group.label}
              </p>
            )}
            {group.items.map(({ href, label, icon: Icon, badge }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                    active
                      ? "bg-blue-600/20 text-blue-400 font-medium"
                      : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {label}
                  {badge && (
                    <span className="ml-auto text-[10px] font-medium bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
                      {badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-700 px-5 py-3">
        {partnerId ? (
          <div>
            <p className="text-[10px] font-semibold text-amber-400 capitalize">{companyName}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">커스텀 세션 활성화됨</p>
          </div>
        ) : (
          <p className="text-[10px] text-slate-500">Stage 1-2 제공 중 &middot; Sample Data</p>
        )}
      </div>
    </aside>
  );
}
