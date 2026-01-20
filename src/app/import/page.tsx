"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AppShell } from "@/components/layout/app-shell";
import type { ParseResult } from "@/lib/types";

interface DraftWithWarnings extends ParseResult {
  file: File;
}

export default function ImportPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [warningMessage, setWarningMessage] = useState<string | null>(null);
  const [errorTitle, setErrorTitle] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (isLoading || isCommitting) {
      return;
    }
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(Array.from(files));
    }
  }, [isLoading, isCommitting]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (isLoading || isCommitting) {
      return;
    }
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(Array.from(files));
    }
  }, [isLoading, isCommitting]);

  const parseSingleFile = async (file: File): Promise<{ ok: boolean; data?: DraftWithWarnings; error?: string }> => {
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
  };

  const commitParseResult = async (target: DraftWithWarnings): Promise<{ ok: boolean; error?: string; rowCount?: number; skippedCount?: number }> => {
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
            // occurredAt 从 API 返回时已经是 ISO 字符串，无需再转换
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
  };

  const handleFiles = async (files: File[]) => {
    if (isLoading || isCommitting) {
      return;
    }
    setError(null);
    setErrorTitle(null);
    setWarningMessage(null);
    setSuccess(null);
    setIsLoading(true);
    setIsCommitting(true);

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

    if (warnings.length > 0) {
      setWarningMessage(warnings.join("；"));
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
      if (successMessage) {
        setErrorTitle("部分失败");
      } else if (hasParseError && hasCommitError) {
        setErrorTitle("处理失败");
      } else if (hasCommitError) {
        setErrorTitle("导入失败");
      } else {
        setErrorTitle("解析失败");
      }
      setError(errors.join("；"));
    }

    if (successMessage) {
      if (errors.length > 0 && totalRowCount === 0 && totalSkippedCount > 0) {
        setSuccess("部分文件已存在，未导入新数据");
      } else {
        setSuccess(successMessage);
      }
    } else if (errors.length === 0) {
      setSuccess("所有记录都已存在，未导入新数据");
    }

    setIsLoading(false);
    setIsCommitting(false);
  };

  const handleReset = () => {
    setWarningMessage(null);
    setErrorTitle(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <main className="min-h-screen bg-background">
      <AppShell title="导入账单" subtitle="账单导入" contentClassName="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* 上传区域 */}
        <Card className="bg-card/80 border-border/70 shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-primary" />
              <CardTitle>上传账单文件</CardTitle>
            </div>
            <CardDescription>拖拽或选择多个文件后自动导入</CardDescription>
          </CardHeader>
          <CardContent>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xls,.xlsx,.pdf"
              multiple
              disabled={isLoading || isCommitting}
              onChange={handleFileInput}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-border/80 hover:border-muted-foreground"
              } ${isLoading || isCommitting ? "pointer-events-none opacity-60" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {isLoading || isCommitting ? (
                <>
                  <Loader2 className="w-12 h-12 text-muted-foreground mb-4 animate-spin" />
                  <p className="text-muted-foreground">正在导入文件...</p>
                </>
              ) : (
                <>
                  <FileSpreadsheet className="w-12 h-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">拖拽文件到此处，或点击选择文件（可多选）</p>
                  <p className="text-sm text-muted-foreground mt-2">最大 10MB，最多 5000 行</p>
                </>
              )}
            </label>
            <p className="text-xs text-muted-foreground mt-3">
              支持格式：支付宝 CSV / 建行 XLS / 招行 PDF（文本可复制）
            </p>
          </CardContent>
        </Card>

        {/* 错误提示 */}
        {error && (
          <Card className="border-destructive bg-card/80 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-destructive">{errorTitle || "处理失败"}</p>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                </div>
                <button onClick={() => setError(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 警告提示 */}
        {warningMessage && (
          <Card className="border-accent bg-card/80 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-accent shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-accent">存在警告</p>
                  <p className="text-sm text-muted-foreground mt-1">{warningMessage}</p>
                </div>
                <button onClick={() => setWarningMessage(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 成功提示 */}
        {success && (
          <Card className="border-primary bg-card/80 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-primary">导入成功</p>
                  <p className="text-sm text-muted-foreground mt-1">{success}</p>
                </div>
                <button onClick={() => setSuccess(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 操作按钮 */}
        {(error || success) && (
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={handleReset} disabled={isCommitting || isLoading}>
              继续导入
            </Button>
            <Button asChild>
              <Link href="/ledger">查看账单</Link>
            </Button>
          </div>
        )}
      </AppShell>
    </main>
  );
}
