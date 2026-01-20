"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BarChart3, Loader2 } from "lucide-react";
import * as echarts from "echarts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

const SOURCE_OPTIONS = [
  { value: "", label: "全部来源" },
  { value: "alipay", label: "支付宝" },
  { value: "ccb", label: "建行" },
  { value: "cmb", label: "招行" },
];

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
};

type CategoryPoint = {
  category: string;
  amount: number;
};

type AccountPoint = {
  accountName: string;
  income: number;
  expense: number;
};

type SourcePoint = {
  source: string;
  income: number;
  expense: number;
};

type CounterpartyPoint = {
  counterparty: string;
  amount: number;
};

type AnalysisPayload = {
  summary: Summary;
  trend: TrendPoint[];
  categories: CategoryPoint[];
  accounts: AccountPoint[];
  sources: SourcePoint[];
  counterparties: CounterpartyPoint[];
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

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getQuickRange(months: number): { start: string; end: string } {
  const end = new Date();
  const start = new Date(end);
  start.setMonth(start.getMonth() - (months - 1));
  start.setDate(1);
  return { start: formatDateInput(start), end: formatDateInput(end) };
}

function formatPeriodLabel(period: string): string {
  const [year, month] = period.split("-");
  return `${year}.${month}`;
}

function TrendChart({ trend }: { trend: TrendPoint[] }): JSX.Element {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || trend.length === 0) {
      return;
    }

    const rootStyle = getComputedStyle(document.documentElement);
    const chart = echarts.init(chartRef.current);
    const categories = trend.map((point) => formatPeriodLabel(point.period));
    const incomeSeries = trend.map((point) => point.income);
    const expenseSeries = trend.map((point) => point.expense);
    const netSeries = trend.map((point) => point.net);

    const option: echarts.EChartsOption = {
      color: [
        rootStyle.getPropertyValue("--color-chart-1").trim(),
        rootStyle.getPropertyValue("--color-chart-2").trim(),
        rootStyle.getPropertyValue("--color-chart-3").trim(),
      ],
      tooltip: {
        trigger: "axis",
        formatter: (params) => {
          const items = Array.isArray(params) ? params : [params];
          const title = items[0]?.axisValueLabel ?? "";
          const rows = items
            .map((item) => {
              const value = typeof item.value === "number" ? item.value : Number(item.value ?? 0);
              const displayValue = Number.isFinite(value) ? value.toFixed(2) : "0.00";
              return `${item.marker}${item.seriesName}：¥${displayValue}`;
            })
            .join("<br/>");
          return `${title}<br/>${rows}`;
        },
      },
      legend: {
        data: ["收入", "支出", "净额"],
        textStyle: { color: rootStyle.getPropertyValue("--color-muted-foreground").trim() },
        bottom: 0,
      },
      grid: {
        left: 44,
        right: 24,
        top: 20,
        bottom: 36,
      },
      xAxis: {
        type: "category",
        data: categories,
        boundaryGap: false,
        axisLine: { lineStyle: { color: rootStyle.getPropertyValue("--color-border").trim() } },
        axisLabel: { color: rootStyle.getPropertyValue("--color-muted-foreground").trim() },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        splitLine: { lineStyle: { color: rootStyle.getPropertyValue("--color-border").trim() } },
        axisLabel: {
          color: rootStyle.getPropertyValue("--color-muted-foreground").trim(),
          formatter: (value: number) => (Math.abs(value) >= 1000 ? `${(value / 1000).toFixed(1)}k` : `${value}`),
        },
      },
      series: [
        {
          name: "收入",
          type: "line",
          data: incomeSeries,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2.6 },
        },
        {
          name: "支出",
          type: "line",
          data: expenseSeries,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2.6 },
        },
        {
          name: "净额",
          type: "line",
          data: netSeries,
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2.2, type: "dashed" },
        },
      ],
    };

    chart.setOption(option);

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [trend]);

  if (trend.length === 0) {
    return <p className="text-sm text-muted-foreground">暂无趋势数据</p>;
  }

  return <div className="w-full h-56" ref={chartRef} />;
}

function BarList({
  items,
  colorClass,
  emptyText,
}: {
  items: { label: string; value: number }[];
  colorClass: string;
  emptyText: string;
}): JSX.Element {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyText}</p>;
  }

  const maxValue = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.label} className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-foreground truncate max-w-[65%]">{item.label}</span>
            <span className="text-muted-foreground font-mono">{formatCurrency(item.value)}</span>
          </div>
          <div className="h-2 rounded-full bg-muted">
            <div
              className={`h-2 rounded-full ${colorClass}`}
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalysisPage(): JSX.Element {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [accountName, setAccountName] = useState("");
  const [source, setSource] = useState("");
  const [accounts, setAccounts] = useState<string[]>([]);
  const [data, setData] = useState<AnalysisPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAccounts = useCallback(async function fetchAccounts(): Promise<void> {
    try {
      const response = await fetch("/api/ledger/accounts");
      const result = await response.json();
      if (result.success) {
        setAccounts(result.data);
      }
    } catch (err) {
      console.error("获取帐号列表失败:", err);
    }
  }, []);

  const fetchAnalysis = useCallback(async function fetchAnalysis(): Promise<void> {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.set("startDate", startDate);
      if (endDate) params.set("endDate", endDate);
      if (accountName) params.set("accountName", accountName);
      if (source) params.set("source", source);

      const response = await fetch(`/api/analysis/summary?${params.toString()}`);
      const result: AnalysisResponse = await response.json();
      if (!result.success) {
        setError(result.error ?? "获取分析数据失败");
        setData(null);
        return;
      }
      setData(result.data ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取分析数据失败");
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [accountName, endDate, source, startDate]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  function handleApply(event: React.FormEvent): void {
    event.preventDefault();
    fetchAnalysis();
  }

  const categoryItems = data?.categories.map((item) => ({
    label: item.category,
    value: item.amount,
  })) ?? [];

  const counterpartyItems = data?.counterparties.map((item) => ({
    label: item.counterparty,
    value: item.amount,
  })) ?? [];

  useEffect(() => {
    if (!data?.dateRange) return;
    if (!startDate && !endDate) {
      setStartDate(data.dateRange.start);
      setEndDate(data.dateRange.end);
    }
  }, [data, endDate, startDate]);

  let content: JSX.Element;
  if (isLoading) {
    content = (
      <Card>
        <CardContent className="pt-6 flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  } else if (error) {
    content = (
      <Card>
        <CardContent className="pt-6 text-center text-sm text-destructive">
          {error}
        </CardContent>
      </Card>
    );
  } else if (data) {
    content = (
      <>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-stagger">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">交易笔数</p>
              <p className="text-2xl font-bold mt-2">{data.summary.totalCount}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">总收入</p>
              <p className="text-2xl font-bold text-primary mt-2">
                {formatCurrency(data.summary.totalIncome)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">总支出</p>
              <p className="text-2xl font-bold text-destructive mt-2">
                {formatCurrency(data.summary.totalExpense)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">净现金流</p>
              <p
                className={`text-2xl font-bold mt-2 ${
                  data.summary.netIncome >= 0 ? "text-primary" : "text-destructive"
                }`}
              >
                {formatCurrency(data.summary.netIncome)}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>收支趋势</CardTitle>
            <CardDescription>按月聚合收入与支出走势</CardDescription>
          </CardHeader>
          <CardContent>
            <TrendChart trend={data.trend} />
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle>支出分类 Top10</CardTitle>
              <CardDescription>聚合消费结构，定位主要花销</CardDescription>
            </CardHeader>
            <CardContent>
              <BarList
                items={categoryItems}
                colorClass="bg-chart-2"
                emptyText="暂无分类支出数据"
              />
            </CardContent>
          </Card>

          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle>对手方 Top10</CardTitle>
              <CardDescription>支出主要流向</CardDescription>
            </CardHeader>
            <CardContent>
              <BarList
                items={counterpartyItems}
                colorClass="bg-chart-4"
                emptyText="暂无对手方数据"
              />
            </CardContent>
          </Card>
        </div>
      </>
    );
  } else {
    content = (
      <Card>
        <CardContent className="pt-6 text-center text-sm text-muted-foreground">
          暂无分析数据
        </CardContent>
      </Card>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <AppShell
        title="分析报表"
        subtitle="收支趋势与结构洞察"
        contentClassName="max-w-7xl mx-auto px-6 pb-16 pt-6 space-y-6"
      >
        <Card className="animate-slide-up">
          <CardContent className="pt-6">
            <form onSubmit={handleApply} className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_1fr_auto]">
              <Input
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
              />
              <Input
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
              />
              <select
                value={accountName}
                onChange={(event) => setAccountName(event.target.value)}
                className="h-10 px-3 rounded-xl border border-input bg-card/70 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">全部帐号</option>
                {accounts.map((account) => (
                  <option key={account} value={account}>
                    {account}
                  </option>
                ))}
              </select>
              <select
                value={source}
                onChange={(event) => setSource(event.target.value)}
                className="h-10 px-3 rounded-xl border border-input bg-card/70 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <Button type="submit">
                <BarChart3 className="w-4 h-4 mr-2" />
                更新
              </Button>
            </form>
            <div className="flex flex-wrap gap-2 mt-3">
              {[3, 6, 12].map((months) => (
                <Button
                  key={months}
                  type="button"
                  variant="outline"
                  onClick={() => {
                    const range = getQuickRange(months);
                    setStartDate(range.start);
                    setEndDate(range.end);
                  }}
                >
                  最近 {months} 个月
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              默认展示全量时间范围，支持按帐号和来源过滤。
            </p>
          </CardContent>
        </Card>

        {content}
      </AppShell>
    </main>
  );
}
