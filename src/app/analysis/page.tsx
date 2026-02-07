"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type Summary = {
  totalCount: number;
  totalExpense: number;
  totalIncome: number;
  netIncome: number;
};

type TrendPoint = {
  period: string;
  income: number;
  expense: number;
  net: number;
  totalCount: number;
};

type AnalysisPayload = {
  summary: Summary;
  monthly: TrendPoint[];
  yearly: TrendPoint[];
  dateRange: {
    start: string;
    end: string;
  } | null;
};

type AnalysisResponse = {
  success: boolean;
  data?: AnalysisPayload;
  error?: string;
};

type ViewMode = "monthly" | "yearly";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatMonth(period: string): string {
  const [year, month] = period.split("-");
  return `${year}年${month}月`;
}

function formatYear(period: string): string {
  return `${period}年`;
}

function SummaryCards({ summary }: { summary: Summary }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>交易笔数</CardDescription>
          <CardTitle className="text-3xl">{summary.totalCount}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>总收入</CardDescription>
          <CardTitle className="text-3xl text-primary">{formatCurrency(summary.totalIncome)}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>总支出</CardDescription>
          <CardTitle className="text-3xl text-destructive">{formatCurrency(summary.totalExpense)}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>净现金流</CardDescription>
          <CardTitle className={`text-3xl ${summary.netIncome >= 0 ? "text-primary" : "text-destructive"}`}>
            {formatCurrency(summary.netIncome)}
          </CardTitle>
        </CardHeader>
      </Card>
    </div>
  );
}

function MonthlySection({ rows }: { rows: TrendPoint[] }) {
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const effectivePeriod = selectedPeriod || rows[rows.length - 1]?.period || "";

  const selectedRow = useMemo(
    () => rows.find((item) => item.period === effectivePeriod) ?? rows[rows.length - 1] ?? null,
    [rows, effectivePeriod]
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">月度概览</CardTitle>
          <CardDescription>按月查看收支趋势，先做一版结构化 DEMO。</CardDescription>
        </CardHeader>
        <CardContent>
          {rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无月度数据</p>
          ) : (
            <select
              value={selectedRow?.period ?? ""}
              onChange={(event) => setSelectedPeriod(event.target.value)}
              className="h-10 w-full rounded-xl border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:w-64"
            >
              {rows.map((row) => (
                <option key={row.period} value={row.period}>
                  {formatMonth(row.period)}
                </option>
              ))}
            </select>
          )}
        </CardContent>
      </Card>

      {selectedRow && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>当前月份</CardDescription>
              <CardTitle className="text-2xl">{formatMonth(selectedRow.period)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>月收入</CardDescription>
              <CardTitle className="text-2xl text-primary">{formatCurrency(selectedRow.income)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>月支出</CardDescription>
              <CardTitle className="text-2xl text-destructive">{formatCurrency(selectedRow.expense)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>月净额</CardDescription>
              <CardTitle className={`text-2xl ${selectedRow.net >= 0 ? "text-primary" : "text-destructive"}`}>
                {formatCurrency(selectedRow.net)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">月度明细</CardTitle>
          <CardDescription>按月份排序，可继续扩展图表区。</CardDescription>
        </CardHeader>
        <CardContent>
          {rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无月度数据</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-border/70">
              <table className="w-full text-sm">
                <thead className="bg-muted/45 text-muted-foreground">
                  <tr className="border-b border-border/70">
                    <th className="px-3 py-2.5 text-left">月份</th>
                    <th className="px-3 py-2.5 text-right">交易笔数</th>
                    <th className="px-3 py-2.5 text-right">收入</th>
                    <th className="px-3 py-2.5 text-right">支出</th>
                    <th className="px-3 py-2.5 text-right">净额</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.period} className="border-b border-border/50">
                      <td className="px-3 py-2.5 font-medium">{formatMonth(row.period)}</td>
                      <td className="px-3 py-2.5 text-right">{row.totalCount}</td>
                      <td className="px-3 py-2.5 text-right text-primary">{formatCurrency(row.income)}</td>
                      <td className="px-3 py-2.5 text-right text-destructive">{formatCurrency(row.expense)}</td>
                      <td className={`px-3 py-2.5 text-right font-medium ${row.net >= 0 ? "text-primary" : "text-destructive"}`}>
                        {formatCurrency(row.net)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function YearlySection({ rows }: { rows: TrendPoint[] }) {
  const latest = rows[rows.length - 1] ?? null;

  return (
    <div className="space-y-4">
      {latest && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>当前年份</CardDescription>
              <CardTitle className="text-2xl">{formatYear(latest.period)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>年收入</CardDescription>
              <CardTitle className="text-2xl text-primary">{formatCurrency(latest.income)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>年支出</CardDescription>
              <CardTitle className="text-2xl text-destructive">{formatCurrency(latest.expense)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>年净额</CardDescription>
              <CardTitle className={`text-2xl ${latest.net >= 0 ? "text-primary" : "text-destructive"}`}>
                {formatCurrency(latest.net)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">年度明细</CardTitle>
          <CardDescription>按自然年汇总，适合看长期变化。</CardDescription>
        </CardHeader>
        <CardContent>
          {rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无年度数据</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-border/70">
              <table className="w-full text-sm">
                <thead className="bg-muted/45 text-muted-foreground">
                  <tr className="border-b border-border/70">
                    <th className="px-3 py-2.5 text-left">年份</th>
                    <th className="px-3 py-2.5 text-right">交易笔数</th>
                    <th className="px-3 py-2.5 text-right">收入</th>
                    <th className="px-3 py-2.5 text-right">支出</th>
                    <th className="px-3 py-2.5 text-right">净额</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.period} className="border-b border-border/50">
                      <td className="px-3 py-2.5 font-medium">{formatYear(row.period)}</td>
                      <td className="px-3 py-2.5 text-right">{row.totalCount}</td>
                      <td className="px-3 py-2.5 text-right text-primary">{formatCurrency(row.income)}</td>
                      <td className="px-3 py-2.5 text-right text-destructive">{formatCurrency(row.expense)}</td>
                      <td className={`px-3 py-2.5 text-right font-medium ${row.net >= 0 ? "text-primary" : "text-destructive"}`}>
                        {formatCurrency(row.net)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AnalysisPage() {
  const [mode, setMode] = useState<ViewMode>("monthly");
  const [data, setData] = useState<AnalysisPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let canceled = false;

    async function fetchAnalysis(): Promise<void> {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/analysis/summary");
        const result: AnalysisResponse = await response.json();
        if (!canceled) {
          if (!result.success) {
            setError(result.error ?? "获取分析数据失败");
            setData(null);
            return;
          }
          setData(result.data ?? null);
        }
      } catch (err) {
        if (!canceled) {
          setError(err instanceof Error ? err.message : "获取分析数据失败");
          setData(null);
        }
      } finally {
        if (!canceled) {
          setIsLoading(false);
        }
      }
    }

    void fetchAnalysis();
    return () => {
      canceled = true;
    };
  }, []);

  return (
    <main className="min-h-screen bg-background">
      <AppShell title="分析报表" subtitle="月度 / 年度 DEMO" contentClassName="mx-auto max-w-7xl space-y-6 px-6 pb-16 pt-6">
        {isLoading ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12 pt-6">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
          </Card>
        ) : !data ? (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">暂无分析数据</CardContent>
          </Card>
        ) : (
          <>
            <Card className="bg-gradient-to-r from-primary/10 via-card to-accent/10">
              <CardContent className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
                <CalendarDays className="h-4 w-4" />
                <span>
                  数据范围: {data.dateRange ? `${data.dateRange.start} 至 ${data.dateRange.end}` : "未识别"}
                </span>
              </CardContent>
            </Card>

            <SummaryCards summary={data.summary} />

            <div className="flex gap-2">
              <Button variant={mode === "monthly" ? "default" : "outline"} onClick={() => setMode("monthly")}>
                月度视图
              </Button>
              <Button variant={mode === "yearly" ? "default" : "outline"} onClick={() => setMode("yearly")}>
                年度视图
              </Button>
            </div>

            {mode === "monthly" ? <MonthlySection rows={data.monthly} /> : <YearlySection rows={data.yearly} />}
          </>
        )}
      </AppShell>
    </main>
  );
}
