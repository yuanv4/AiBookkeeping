"use client";

import type { ReactNode } from "react";
import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AlertCircle, BarChart3, CheckCircle, FileSpreadsheet, Loader2, Sparkles, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ParseResult } from "@/lib/types";

type AppShellProps = {
  title?: string;
  subtitle?: string;
  contentClassName?: string;
  children: ReactNode;
};

const navItems = [
  { href: "/ledger", label: "账单明细", icon: FileSpreadsheet, accent: "text-accent" },
  { href: "/analysis", label: "分析报表", icon: BarChart3, accent: "text-primary" },
];

type ImportStatusTone = "success" | "warning" | "error";

type ImportStatus = {
  tone: ImportStatusTone;
  title: string;
  message: string;
};

interface DraftWithWarnings extends ParseResult {
  file: File;
}

export function AppShell({
  title,
  subtitle,
  contentClassName = "max-w-7xl mx-auto px-6 pb-16 pt-6 space-y-6",
  children,
}: AppShellProps): JSX.Element {
  const pathname = usePathname();
  const [isImporting, setIsImporting] = useState(false);
  const [status, setStatus] = useState<ImportStatus | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const baseItemClass = "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-colors";
  const inactiveItemClass =
    "border border-border/70 bg-card/70 text-foreground/80 hover:border-primary/40 hover:text-foreground";
  const activeItemClass = "bg-primary text-primary-foreground shadow-sm";

  const parseSingleFile = useCallback(async function parseSingleFile(
    file: File
  ): Promise<{ ok: boolean; data?: DraftWithWarnings; error?: string }> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/import/parse", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!result.success) {
        return { ok: false, error: result.error || "解析失败" };
      }

      return { ok: true, data: { ...result.data, file } };
    } catch (err) {
      return { ok: false, error: err instanceof Error ? err.message : "上传失败" };
    }
  }, []);

  const commitParseResult = useCallback(async function commitParseResult(
    target: DraftWithWarnings
  ): Promise<{ ok: boolean; error?: string; rowCount?: number; skippedCount?: number }> {
    try {
      const response = await fetch("/api/import/commit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fileName: target.file.name,
          fileSize: target.file.size,
          source: target.source,
          sourceType: target.sourceType,
          drafts: target.drafts.map((d) => ({
            ...d,
            occurredAt: typeof d.occurredAt === "string"
              ? d.occurredAt
              : (d.occurredAt as Date).toISOString(),
          })),
          warningCount: target.warnings.length,
        }),
      });

      const result = await response.json();

      if (!result.success) {
        return { ok: false, error: result.error || "导入失败" };
      }

      const { rowCount, skippedCount } = result.data;
      return { ok: true, rowCount, skippedCount };
    } catch (err) {
      return { ok: false, error: err instanceof Error ? err.message : "导入失败" };
    }
  }, []);

  const handleFiles = useCallback(async function handleFiles(files: File[]): Promise<void> {
    if (isImporting) {
      return;
    }
    setStatus(null);
    setIsImporting(true);

    const errors: string[] = [];
    const warnings: string[] = [];
    let hasParseError = false;
    let hasCommitError = false;
    let totalRowCount = 0;
    let totalSkippedCount = 0;

    for (const file of files) {
      const parseResult = await parseSingleFile(file);
      if (!parseResult.ok || !parseResult.data) {
        errors.push(`${file.name}：${parseResult.error || "解析失败"}`);
        hasParseError = true;
        continue;
      }
      if (parseResult.data.warnings.length > 0) {
        const warningSamples = parseResult.data.warnings.slice(0, 2);
        const warningSampleText = warningSamples
          .map((warning) => `第 ${warning.row} 行 ${warning.message}`)
          .join("，");
        const warningSuffix = parseResult.data.warnings.length > warningSamples.length ? " 等" : "";
        warnings.push(`${file.name}：${parseResult.data.warnings.length} 条警告，例如 ${warningSampleText}${warningSuffix}`);
      }
      const commitResult = await commitParseResult(parseResult.data);
      if (!commitResult.ok) {
        errors.push(`${file.name}：${commitResult.error || "导入失败"}`);
        hasCommitError = true;
        continue;
      }

      totalRowCount += commitResult.rowCount || 0;
      totalSkippedCount += commitResult.skippedCount || 0;
    }

    let successMessage: string | null = null;
    if (totalRowCount === 0 && totalSkippedCount > 0) {
      successMessage = "所有记录都已存在，未导入新数据";
    } else if (totalRowCount > 0 && totalSkippedCount > 0) {
      successMessage = `成功导入 ${totalRowCount} 条交易记录，跳过 ${totalSkippedCount} 条重复记录`;
    } else if (totalRowCount > 0) {
      successMessage = `成功导入 ${totalRowCount} 条交易记录`;
    }

    if (errors.length > 0) {
      let title = "解析失败";
      if (successMessage) {
        title = "部分失败";
      } else if (hasParseError && hasCommitError) {
        title = "处理失败";
      } else if (hasCommitError) {
        title = "导入失败";
      }
      const message = successMessage ? `${errors.join("；")}；${successMessage}` : errors.join("；");
      setStatus({ tone: "error", title, message });
      setIsImporting(false);
      return;
    }

    if (warnings.length > 0) {
      const message = successMessage ? `${successMessage}；${warnings.join("；")}` : warnings.join("；");
      setStatus({ tone: "warning", title: "存在警告", message });
      setIsImporting(false);
      return;
    }

    setStatus({
      tone: "success",
      title: "导入完成",
      message: successMessage || "所有记录都已存在，未导入新数据",
    });
    setIsImporting(false);
  }, [commitParseResult, isImporting, parseSingleFile]);

  const handleFileInput = useCallback(function handleFileInput(
    event: React.ChangeEvent<HTMLInputElement>
  ): void {
    if (isImporting) {
      return;
    }
    const files = event.target.files;
    if (files && files.length > 0) {
      void handleFiles(Array.from(files));
    }
    event.target.value = "";
  }, [handleFiles, isImporting]);

  const handleOpenPicker = useCallback(function handleOpenPicker(): void {
    if (!isImporting) {
      fileInputRef.current?.click();
    }
  }, [isImporting]);

  const statusConfig = status
    ? (() => {
        if (status.tone === "success") {
          return {
            icon: CheckCircle,
            className: "border border-primary/40",
            iconClassName: "text-primary",
            titleClassName: "text-primary",
          };
        }
        if (status.tone === "warning") {
          return {
            icon: AlertCircle,
            className: "border border-accent/40",
            iconClassName: "text-accent",
            titleClassName: "text-accent",
          };
        }
        return {
          icon: AlertCircle,
          className: "border border-destructive/40",
          iconClassName: "text-destructive",
          titleClassName: "text-destructive",
        };
      })()
    : null;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-border/60 bg-background/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-2xl border border-border/70 bg-card/80 flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-lg leading-tight tracking-tight">账单汇总</p>
              <p className="text-xs text-muted-foreground">多来源清洗与对账</p>
            </div>
            <span className="stamp-badge">
              <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              个人账本
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xls,.xlsx,.pdf"
              multiple
              onChange={handleFileInput}
              className="hidden"
            />
            <Button
              onClick={handleOpenPicker}
              disabled={isImporting}
              variant="outline"
              className="border-primary/40 text-primary hover:bg-primary/10"
            >
              {isImporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              {isImporting ? "导入中..." : "导入账单"}
            </Button>
            <nav className="flex flex-wrap gap-2">
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
        </div>
      </header>

      {(status || isImporting) && (
        <section className="max-w-7xl mx-auto px-6 pt-6">
          <Card className={statusConfig?.className ?? "border border-border/60"}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                {status && statusConfig ? (
                  <statusConfig.icon className={`w-5 h-5 shrink-0 mt-0.5 ${statusConfig.iconClassName}`} />
                ) : (
                  <Loader2 className="w-5 h-5 shrink-0 mt-0.5 animate-spin text-muted-foreground" />
                )}
                <div className="flex-1">
                  <p className={`font-medium ${statusConfig?.titleClassName ?? "text-foreground"}`}>
                    {status?.title ?? "正在导入账单"}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {status?.message ?? "文件解析与写入中，请稍候。"}
                  </p>
                </div>
                {status && (
                  <button onClick={() => setStatus(null)} className="text-muted-foreground hover:text-foreground">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </CardContent>
          </Card>
        </section>
      )}

      {(title || subtitle) && (
        <section className="max-w-7xl mx-auto px-6 pt-8">
          <div className="paper-panel p-6 sm:p-8">
            {subtitle && <p className="text-sm text-muted-foreground ink-label">{subtitle}</p>}
            {title && <h1 className="text-3xl sm:text-4xl font-semibold mt-3">{title}</h1>}
          </div>
        </section>
      )}

      <div className={contentClassName}>{children}</div>
    </div>
  );
}
