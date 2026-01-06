"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, Upload, FileSpreadsheet, AlertCircle, CheckCircle, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ParseResult, UnifiedTransactionDraft, ParseWarning, BillSource } from "@/lib/types";

type FileType = "csv" | "xls" | "pdf";

interface DraftWithWarnings extends ParseResult {
  file: File;
}

export default function ImportPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [parseResult, setParseResult] = useState<DraftWithWarnings | null>(null);
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
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, []);

  const handleFile = async (file: File) => {
    setError(null);
    setSuccess(null);
    setParseResult(null);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/import/parse", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!result.success) {
        setError(result.error || "解析失败");
        return;
      }

      setParseResult({ ...result.data, file });
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setParseResult(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleCommit = async () => {
    if (!parseResult) return;

    setIsCommitting(true);
    setError(null);

    try {
      const response = await fetch("/api/import/commit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fileName: parseResult.file.name,
          fileSize: parseResult.file.size,
          source: parseResult.source,
          sourceType: parseResult.sourceType,
          drafts: parseResult.drafts.map((d) => ({
            ...d,
            // occurredAt 从 API 返回时已经是 ISO 字符串，无需再转换
            occurredAt: typeof d.occurredAt === 'string' 
              ? d.occurredAt 
              : (d.occurredAt as Date).toISOString(),
          })),
          warningCount: parseResult.warnings.length,
        }),
      });

      const result = await response.json();

      if (!result.success) {
        setError(result.error || "导入失败");
        return;
      }

      const { rowCount, skippedCount } = result.data;
      if (rowCount === 0) {
        setSuccess("所有记录都已存在，未导入新数据");
      } else if (skippedCount > 0) {
        setSuccess(`成功导入 ${rowCount} 条交易记录，跳过 ${skippedCount} 条重复记录`);
      } else {
        setSuccess(`成功导入 ${rowCount} 条交易记录`);
      }
      setParseResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "导入失败");
    } finally {
      setIsCommitting(false);
    }
  };

  const getSourceName = (source: BillSource): string => {
    switch (source) {
      case "alipay": return "支付宝";
      case "ccb": return "建设银行";
      case "cmb": return "招商银行";
      default: return source;
    }
  };

  const formatAmount = (amount: number, direction: string): string => {
    const sign = direction === "out" ? "-" : "+";
    return `${sign}¥${amount.toFixed(2)}`;
  };

  const formatDate = (date: Date): string => {
    return new Date(date).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <main className="min-h-screen bg-background">
      {/* 导航栏 */}
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/" className="text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-semibold text-lg">导入账单</h1>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* 上传区域 */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-primary" />
              <CardTitle>上传账单文件</CardTitle>
            </div>
            <CardDescription>
              支持支付宝 CSV、建设银行 XLS、招商银行 PDF（仅限可复制文本）
            </CardDescription>
          </CardHeader>
          <CardContent>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xls,.xlsx,.pdf"
              onChange={handleFileInput}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-muted-foreground"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-12 h-12 text-muted-foreground mb-4 animate-spin" />
                  <p className="text-muted-foreground">正在解析文件...</p>
                </>
              ) : (
                <>
                  <FileSpreadsheet className="w-12 h-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">拖拽文件到此处，或点击选择文件</p>
                  <p className="text-sm text-muted-foreground mt-2">最大 10MB，最多 5000 行</p>
                </>
              )}
            </label>
          </CardContent>
        </Card>

        {/* 错误提示 */}
        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-destructive">解析失败</p>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                </div>
                <button onClick={() => setError(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 成功提示 */}
        {success && (
          <Card className="border-primary">
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

        {/* 导入说明 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-accent shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">导入说明</p>
                <ul className="list-disc list-inside text-sm text-muted-foreground mt-2 space-y-1">
                  <li>支付宝账单请从支付宝 APP 导出 CSV 格式</li>
                  <li>建设银行账单请从网银导出 XLS 格式</li>
                  <li>招商银行账单请从掌上生活导出 PDF（确保文字可复制）</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 解析预览 */}
        {parseResult && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>解析预览</CardTitle>
                  <CardDescription className="mt-1">
                    来源: {getSourceName(parseResult.source)} | 
                    格式: {parseResult.sourceType.toUpperCase()} | 
                    共 {parseResult.rowCount} 条记录
                    {parseResult.warnings.length > 0 && (
                      <span className="text-accent"> | {parseResult.warnings.length} 条警告</span>
                    )}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* 警告信息 */}
              {parseResult.warnings.length > 0 && (
                <div className="mb-4 p-3 bg-accent/10 rounded-lg">
                  <p className="text-sm font-medium text-accent mb-2">
                    解析警告（{parseResult.warnings.length} 条）
                  </p>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {parseResult.warnings.slice(0, 5).map((w, i) => (
                      <li key={i}>第 {w.row} 行: {w.message}</li>
                    ))}
                    {parseResult.warnings.length > 5 && (
                      <li>... 还有 {parseResult.warnings.length - 5} 条警告</li>
                    )}
                  </ul>
                </div>
              )}

              {/* 数据预览表格 */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4 font-medium">时间</th>
                      <th className="text-left py-3 px-4 font-medium">对方</th>
                      <th className="text-left py-3 px-4 font-medium">描述</th>
                      <th className="text-right py-3 px-4 font-medium">金额</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parseResult.drafts.slice(0, 10).map((draft, index) => (
                      <tr key={index} className="border-b border-border/50">
                        <td className="py-3 px-4 text-muted-foreground">
                          {formatDate(draft.occurredAt)}
                        </td>
                        <td className="py-3 px-4">{draft.counterparty || "-"}</td>
                        <td className="py-3 px-4 text-muted-foreground truncate max-w-[200px]">
                          {draft.description || draft.category || "-"}
                        </td>
                        <td className={`py-3 px-4 text-right font-medium ${
                          draft.direction === "out" ? "text-destructive" : "text-primary"
                        }`}>
                          {formatAmount(draft.amount, draft.direction)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {parseResult.drafts.length > 10 && (
                <p className="text-sm text-muted-foreground mt-3 text-center">
                  ... 还有 {parseResult.drafts.length - 10} 条记录
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!parseResult && !error && !success}
          >
            重新选择
          </Button>
          <Button
            onClick={handleCommit}
            disabled={!parseResult || isCommitting}
          >
            {isCommitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                导入中...
              </>
            ) : (
              "确认导入"
            )}
          </Button>
        </div>
      </div>
    </main>
  );
}
