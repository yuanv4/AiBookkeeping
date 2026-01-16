"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileSpreadsheet, Sparkles, Upload } from "lucide-react";

type AppShellProps = {
  title?: string;
  subtitle?: string;
  contentClassName?: string;
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "主页概览", icon: Sparkles, accent: "text-primary" },
  { href: "/ledger", label: "统一账单", icon: FileSpreadsheet, accent: "text-accent" },
  { href: "/import", label: "设置", icon: Upload, accent: "text-primary" },
];

export function AppShell({
  title,
  subtitle,
  contentClassName = "px-6 py-8",
  children,
}: AppShellProps) {
  const pathname = usePathname();
  const baseItemClass = "flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium";
  const inactiveItemClass =
    "border border-border/70 bg-card/80 text-foreground hover:border-primary/50 transition-colors";
  const activeItemClass = "bg-foreground text-background";

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 border-r border-border/70 bg-background/80 backdrop-blur-sm sticky top-0 h-screen">
        <div className="h-full flex flex-col px-6 py-6">
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 rounded-lg bg-foreground text-background flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <p className="font-semibold text-lg leading-tight">AI 智能记账</p>
              <p className="text-xs text-muted-foreground">统一账单管理</p>
            </div>
          </div>
          <nav className="space-y-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const ItemIcon = item.icon;
              const itemClassName = `${baseItemClass} ${isActive ? activeItemClass : inactiveItemClass}`;
              const iconClassName = isActive ? "w-4 h-4" : `w-4 h-4 ${item.accent}`;

              return isActive ? (
                <span key={item.href} className={itemClassName}>
                  <ItemIcon className={iconClassName} />
                  {item.label}
                </span>
              ) : (
                <Link key={item.href} href={item.href} className={itemClassName}>
                  <ItemIcon className={iconClassName} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      <div className="flex-1">
        {(title || subtitle) && (
          <header className="border-b border-border/70 bg-background/60">
            <div className="max-w-7xl mx-auto px-6 py-6">
              {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
              {title && <h1 className="text-2xl font-semibold">{title}</h1>}
            </div>
          </header>
        )}
        <div className={contentClassName}>{children}</div>
      </div>
    </div>
  );
}
