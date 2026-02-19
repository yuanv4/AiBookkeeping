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

function getPeriodYear(period: string): string {
  return period.split("-")[0] ?? "";
}

function getPeriodMonth(period: string): string {
  return period.split("-")[1] ?? "";
}

function formatMonth(period: string): string {
  return `${getPeriodYear(period)}年${getPeriodMonth(period)}月`;
}

function formatYear(period: string): string {
  return `${period}年`;
}

function SummaryCards({ summary }: { summary: Summary }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card className="border-primary/20">
        <CardHeader className="pb-2">
          <CardDescription>交易笔数</CardDescription>
          <CardTitle className="text-3xl">{summary.totalCount}</CardTitle>
        </CardHeader>
      </Card>
      <Card className="border-primary/20">
        <CardHeader className="pb-2">
          <CardDescription>总收入</CardDescription>
          <CardTitle className="text-3xl text-primary">{formatCurrency(summary.totalIncome)}</CardTitle>
        </CardHeader>
      </Card>
      <Card className="border-destructive/20">
        <CardHeader className="pb-2">
          <CardDescription>总支出</CardDescription>
          <CardTitle className="text-3xl text-destructive">{formatCurrency(summary.totalExpense)}</CardTitle>
        </CardHeader>
      </Card>
      <Card className={`${summary.netIncome >= 0 ? "border-primary/20" : "border-destructive/20"}`}>
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

function NetTrendBars({ rows }: { rows: TrendPoint[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground">暂无趋势数据</p>;
  }

  const maxAbsNet = Math.max(...rows.map((item) => Math.abs(item.net)), 1);

  return (
    <div className="space-y-3">
      {rows.map((row) => {
        const width = `${(Math.abs(row.net) / maxAbsNet) * 100}%`;
        const tone = row.net >= 0 ? "bg-primary/70" : "bg-destructive/70";
        return (
          <div key={row.period} className="grid grid-cols-[88px_1fr_120px] items-center gap-3 text-sm">
            <span className="text-muted-foreground">{formatMonth(row.period)}</span>
            <div className="h-2.5 rounded-full bg-muted">
              <div className={`h-full rounded-full ${tone}`} style={{ width }} />
            </div>
            <span className={`text-right font-medium ${row.net >= 0 ? "text-primary" : "text-destructive"}`}>
              {formatCurrency(row.net)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function MonthlySection({
  rows,
  selectedYear,
  onSelectYear,
}: {
  rows: TrendPoint[];
  selectedYear: string;
  onSelectYear: (year: string) => void;
}) {
  const years = useMemo(() => Array.from(new Set(rows.map((item) => getPeriodYear(item.period)))).sort(), [rows]);

  const filteredRows = useMemo(() => {
    if (!selectedYear) return rows;
    return rows.filter((item) => getPeriodYear(item.period) === selectedYear);
  }, [rows, selectedYear]);

  const [selectedPeriod, setSelectedPeriod] = useState("");
  const effectivePeriod = useMemo(() => {
    if (filteredRows.some((item) => item.period === selectedPeriod)) {
      return selectedPeriod;
    }
    return filteredRows[filteredRows.length - 1]?.period ?? "";
  }, [filteredRows, selectedPeriod]);

  const selectedRow = useMemo(
    () => filteredRows.find((item) => item.period === effectivePeriod) ?? filteredRows[filteredRows.length - 1] ?? null,
    [filteredRows, effectivePeriod]
  );

  return (
    <div className="space-y-4">
      <Card className="border-border/70 bg-gradient-to-r from-primary/10 via-card to-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">月度视图</CardTitle>
          <CardDescription>按年份筛选月份，重点看每个月净额变化。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {years.map((year) => (
              <Button
                key={year}
                variant={selectedYear === year ? "default" : "outline"}
                size="sm"
                onClick={() => onSelectYear(year)}
              >
                {year}年
              </Button>
            ))}
          </div>
          {filteredRows.length > 0 && (
            <select
              value={selectedRow?.period ?? ""}
              onChange={(event) => setSelectedPeriod(event.target.value)}
              className="h-10 w-full rounded-xl border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:w-72"
            >
              {filteredRows.map((row) => (
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
          <CardTitle className="text-xl">月度净额趋势</CardTitle>
          <CardDescription>{selectedYear ? `${selectedYear} 年各月净额` : "各月净额"}</CardDescription>
        </CardHeader>
        <CardContent>
          <NetTrendBars rows={filteredRows} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">月度明细</CardTitle>
          <CardDescription>该表用于快速核对月度收支。</CardDescription>
        </CardHeader>
        <CardContent>
          {filteredRows.length === 0 ? (
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
                  {filteredRows.map((row) => (
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

function YearlySection({
  rows,
  selectedYear,
  onJumpToMonthly,
}: {
  rows: TrendPoint[];
  selectedYear: string;
  onJumpToMonthly: (year: string) => void;
}) {
  const latest = rows[rows.length - 1] ?? null;
  const focus = rows.find((row) => row.period === selectedYear) ?? latest;

  return (
    <div className="space-y-4">
      {focus && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>当前年份</CardDescription>
              <CardTitle className="text-2xl">{formatYear(focus.period)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>年收入</CardDescription>
              <CardTitle className="text-2xl text-primary">{formatCurrency(focus.income)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>年支出</CardDescription>
              <CardTitle className="text-2xl text-destructive">{formatCurrency(focus.expense)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>年净额</CardDescription>
              <CardTitle className={`text-2xl ${focus.net >= 0 ? "text-primary" : "text-destructive"}`}>
                {formatCurrency(focus.net)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xl">年度明细</CardTitle>
          <CardDescription>点击“查看月度”可跳回对应年份的月度视图。</CardDescription>
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
                    <th className="px-3 py-2.5 text-right">操作</th>
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
                      <td className="px-3 py-2.5 text-right">
                        <Button size="sm" variant="outline" onClick={() => onJumpToMonthly(row.period)}>
                          查看月度
                        </Button>
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
  const [selectedYear, setSelectedYear] = useState("");
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
          const payload = result.data ?? null;
          setData(payload);

          const lastMonthlyPeriod = payload?.monthly[payload.monthly.length - 1]?.period ?? "";
          if (lastMonthlyPeriod) {
            setSelectedYear(getPeriodYear(lastMonthlyPeriod));
          }
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

  function handleJumpToMonthly(year: string): void {
    setSelectedYear(year);
    setMode("monthly");
  }

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
            <Card className="border-border/70 bg-gradient-to-r from-primary/10 via-card to-accent/10">
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

            {mode === "monthly" ? (
              <MonthlySection rows={data.monthly} selectedYear={selectedYear} onSelectYear={setSelectedYear} />
            ) : (
              <YearlySection rows={data.yearly} selectedYear={selectedYear} onJumpToMonthly={handleJumpToMonthly} />
            )}
          </>
        )}
      </AppShell>
    </main>
  );
}
