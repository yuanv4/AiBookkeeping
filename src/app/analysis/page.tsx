"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  BarChart3,
  CalendarDays,
  CircleDollarSign,
  Landmark,
  Loader2,
  RotateCcw,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import * as echarts from "echarts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

const SOURCE_OPTIONS = [
  { value: "", label: "全部来源" },
  { value: "alipay", label: "支付宝" },
  { value: "ccb", label: "建设银行" },
  { value: "cmb", label: "招商银行" },
] as const;

const SOURCE_NAME_MAP: Record<string, string> = {
  alipay: "支付宝",
  ccb: "建设银行",
  cmb: "招商银行",
};

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

type AlipayAnalysis = {
  summary: Summary;
  monthly: TrendPoint[];
  categories: CategoryPoint[];
  counterparties: CounterpartyPoint[];
  accounts: AccountPoint[];
};

type AnalysisPayload = {
  summary: Summary;
  monthly: TrendPoint[];
  yearly: TrendPoint[];
  trend: TrendPoint[];
  categories: CategoryPoint[];
  accounts: AccountPoint[];
  sources: SourcePoint[];
  counterparties: CounterpartyPoint[];
  alipay: AlipayAnalysis;
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

type Filters = {
  startDate: string;
  endDate: string;
  accountName: string;
  source: string;
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

function SectionHeading({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-4 flex items-start gap-3">
      <span className="mt-1 h-6 w-1.5 rounded-full bg-gradient-to-b from-primary to-accent" />
      <div>
        <h3 className="text-xl font-semibold leading-tight">{title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

function TrendChart({ trend }: { trend: TrendPoint[] }) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || trend.length === 0) return;

    const rootStyle = getComputedStyle(document.documentElement);
    const chart = echarts.init(chartRef.current);
    const categories = trend.map((point) => formatPeriodLabel(point.period));

    const option: echarts.EChartsOption = {
      color: [
        rootStyle.getPropertyValue("--color-chart-1").trim(),
        rootStyle.getPropertyValue("--color-chart-2").trim(),
        rootStyle.getPropertyValue("--color-chart-3").trim(),
      ],
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(24, 32, 40, 0.92)",
        borderWidth: 0,
        textStyle: { color: "#f9f7f3" },
        formatter: (params: unknown) => {
          const items = (Array.isArray(params) ? params : [params]) as Array<{
            axisValueLabel?: string;
            axisValue?: string | number;
            marker?: string;
            seriesName?: string;
            value?: string | number;
          }>;

          const first = items[0];
          const title = first?.axisValueLabel ?? String(first?.axisValue ?? "");
          const rows = items
            .map((item) => {
              const rawValue = item.value;
              const value = typeof rawValue === "number" ? rawValue : Number(rawValue ?? 0);
              const display = Number.isFinite(value) ? formatCurrency(value) : formatCurrency(0);
              return `${item.marker ?? ""}${item.seriesName ?? ""}：${display}`;
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
        right: 20,
        top: 24,
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
          data: trend.map((point) => point.income),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2.6 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(21, 84, 62, 0.22)" },
              { offset: 1, color: "rgba(21, 84, 62, 0.02)" },
            ]),
          },
        },
        {
          name: "支出",
          type: "line",
          data: trend.map((point) => point.expense),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 2.6 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(198, 88, 36, 0.18)" },
              { offset: 1, color: "rgba(198, 88, 36, 0.02)" },
            ]),
          },
        },
        {
          name: "净额",
          type: "line",
          data: trend.map((point) => point.net),
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

  return <div className="h-64 w-full" ref={chartRef} />;
}

function MetricCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone: "neutral" | "income" | "expense";
}) {
  const toneStyles =
    tone === "income"
      ? "border-primary/45 from-primary/14 via-card to-primary/5 text-primary"
      : tone === "expense"
        ? "border-destructive/35 from-destructive/12 via-card to-destructive/5 text-destructive"
        : "border-border/70 from-card via-card to-muted/35 text-foreground";

  return (
    <Card className={`overflow-hidden border ${toneStyles}`}>
      <CardContent className="pb-5 pt-5">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-br opacity-80" />
        <div className="relative">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border/60 bg-background/75">
              {icon}
            </span>
          </div>
          <p className="mt-3 text-2xl font-semibold">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function BarList({
  items,
  colorClass,
  emptyText,
}: {
  items: { label: string; value: number }[];
  colorClass: string;
  emptyText: string;
}) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyText}</p>;
  }

  const maxValue = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="space-y-4">
      {items.map((item, index) => {
        const percentage = (item.value / maxValue) * 100;
        return (
          <div key={`${item.label}-${index}`} className="space-y-2">
            <div className="flex items-center justify-between gap-3 text-sm">
              <div className="min-w-0 flex items-center gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-border/60 bg-background text-xs font-semibold text-muted-foreground">
                  {index + 1}
                </span>
                <span className="truncate font-medium">{item.label}</span>
              </div>
              <span className="whitespace-nowrap font-mono text-muted-foreground">{formatCurrency(item.value)}</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-muted">
              <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${percentage}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BreakdownTable({
  title,
  description,
  rows,
}: {
  title: string;
  description: string;
  rows: Array<{ label: string; income: number; expense: number }>;
}) {
  const totalFlow = rows.reduce((sum, row) => sum + row.income + row.expense, 0);

  return (
    <Card className="animate-slide-up overflow-hidden border-border/70">
      <CardHeader className="pb-3">
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无数据</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border/70">
            <table className="w-full text-sm">
              <thead className="bg-muted/45 text-xs uppercase tracking-[0.12em] text-muted-foreground">
                <tr className="border-b border-border/70">
                  <th className="px-3 py-3 text-left">名称</th>
                  <th className="px-3 py-3 text-right">收入</th>
                  <th className="px-3 py-3 text-right">支出</th>
                  <th className="px-3 py-3 text-right">净额</th>
                  <th className="px-3 py-3 text-right">占比</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 8).map((row) => {
                  const flow = row.income + row.expense;
                  const ratio = totalFlow > 0 ? (flow / totalFlow) * 100 : 0;
                  const net = row.income - row.expense;
                  return (
                    <tr key={row.label} className="border-b border-border/50 hover:bg-muted/25">
                      <td className="px-3 py-2.5 font-medium">{row.label}</td>
                      <td className="px-3 py-2.5 text-right text-primary">{formatCurrency(row.income)}</td>
                      <td className="px-3 py-2.5 text-right text-destructive">{formatCurrency(row.expense)}</td>
                      <td className={`px-3 py-2.5 text-right font-medium ${net >= 0 ? "text-primary" : "text-destructive"}`}>
                        {formatCurrency(net)}
                      </td>
                      <td className="px-3 py-2.5 text-right text-muted-foreground">{ratio.toFixed(1)}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function YearlySummaryTable({ rows }: { rows: TrendPoint[] }) {
  return (
    <Card className="animate-slide-up overflow-hidden border-border/70">
      <CardHeader className="pb-3">
        <CardTitle className="text-xl">年度汇总</CardTitle>
        <CardDescription>按自然年查看全年收支和净现金流</CardDescription>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无年度数据</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border/70">
            <table className="w-full text-sm">
              <thead className="bg-muted/45 text-xs uppercase tracking-[0.12em] text-muted-foreground">
                <tr className="border-b border-border/70">
                  <th className="px-3 py-3 text-left">年份</th>
                  <th className="px-3 py-3 text-right">交易笔数</th>
                  <th className="px-3 py-3 text-right">收入</th>
                  <th className="px-3 py-3 text-right">支出</th>
                  <th className="px-3 py-3 text-right">净额</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.period} className="border-b border-border/50 hover:bg-muted/25">
                    <td className="px-3 py-2.5 font-medium">{row.period}</td>
                    <td className="px-3 py-2.5 text-right text-muted-foreground">{row.totalCount}</td>
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
  );
}

export default function AnalysisPage() {
  const [filters, setFilters] = useState<Filters>({ startDate: "", endDate: "", accountName: "", source: "" });
  const [accounts, setAccounts] = useState<string[]>([]);
  const [data, setData] = useState<AnalysisPayload | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAccounts = useCallback(async function fetchAccounts(): Promise<void> {
    try {
      const response = await fetch("/api/ledger/accounts");
      const result = await response.json();
      if (result.success) setAccounts(result.data);
    } catch (err) {
      console.error("获取账户列表失败:", err);
    }
  }, []);

  const fetchAnalysis = useCallback(async function fetchAnalysis(targetFilters: Filters): Promise<void> {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (targetFilters.startDate) params.set("startDate", targetFilters.startDate);
      if (targetFilters.endDate) params.set("endDate", targetFilters.endDate);
      if (targetFilters.accountName) params.set("accountName", targetFilters.accountName);
      if (targetFilters.source) params.set("source", targetFilters.source);

      const response = await fetch(`/api/analysis/summary?${params.toString()}`);
      const result: AnalysisResponse = await response.json();

      if (!result.success) {
        setError(result.error ?? "获取分析数据失败");
        setData(null);
        return;
      }

      setData(result.data ?? null);

      if (result.data?.dateRange && !targetFilters.startDate && !targetFilters.endDate) {
        setFilters((prev) => ({
          ...prev,
          startDate: result.data?.dateRange?.start ?? prev.startDate,
          endDate: result.data?.dateRange?.end ?? prev.endDate,
        }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取分析数据失败");
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchAccounts();
  }, [fetchAccounts]);

  useEffect(() => {
    void fetchAnalysis(filters);
    // initial load only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const dateRangeLabel = useMemo(() => {
    if (!data?.dateRange) return "-";
    return `${data.dateRange.start} 至 ${data.dateRange.end}`;
  }, [data]);

  const activeFilterLabel = useMemo(() => {
    const labels: string[] = [];
    if (filters.accountName) labels.push(`账户：${filters.accountName}`);
    if (filters.source) labels.push(`来源：${SOURCE_NAME_MAP[filters.source] ?? filters.source}`);
    if (filters.startDate || filters.endDate) labels.push(`日期：${filters.startDate || "最早"} ~ ${filters.endDate || "最新"}`);
    return labels.length > 0 ? labels.join("；") : "未设置筛选";
  }, [filters]);

  const categoryItems = data?.categories.map((item) => ({ label: item.category, value: item.amount })) ?? [];
  const counterpartyItems = data?.counterparties.map((item) => ({ label: item.counterparty, value: item.amount })) ?? [];
  const alipayCategoryItems = data?.alipay.categories.map((item) => ({ label: item.category, value: item.amount })) ?? [];
  const alipayCounterpartyItems = data?.alipay.counterparties.map((item) => ({ label: item.counterparty, value: item.amount })) ?? [];

  function updateFilter<K extends keyof Filters>(key: K, value: Filters[K]): void {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function handleApply(event: React.FormEvent): void {
    event.preventDefault();
    void fetchAnalysis(filters);
  }

  function handleQuickRange(months: number): void {
    const range = getQuickRange(months);
    const next = { ...filters, startDate: range.start, endDate: range.end };
    setFilters(next);
    void fetchAnalysis(next);
  }

  function handleReset(): void {
    const next: Filters = { startDate: "", endDate: "", accountName: "", source: "" };
    setFilters(next);
    void fetchAnalysis(next);
  }

  function isQuickRangeActive(months: number): boolean {
    const range = getQuickRange(months);
    return filters.startDate === range.start && filters.endDate === range.end;
  }

  let content: ReactNode;

  if (isLoading) {
    content = (
      <Card>
        <CardContent className="flex items-center justify-center py-12 pt-6">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  } else if (error) {
    content = (
      <Card>
        <CardContent className="pt-6 text-center text-sm text-destructive">{error}</CardContent>
      </Card>
    );
  } else if (!data) {
    content = (
      <Card>
        <CardContent className="pt-6 text-center text-sm text-muted-foreground">暂无分析数据</CardContent>
      </Card>
    );
  } else {
    content = (
      <>
        <Card className="animate-slide-up border-border/70 bg-gradient-to-r from-primary/10 via-card to-accent/10">
          <CardContent className="grid grid-cols-1 gap-3 pb-5 pt-5 text-sm md:grid-cols-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              <span>数据范围：{dateRangeLabel}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <CircleDollarSign className="h-4 w-4" />
              <span>筛选条件：{activeFilterLabel}</span>
            </div>
          </CardContent>
        </Card>

        <div className="animate-stagger grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={<BarChart3 className="h-4 w-4" />} label="交易笔数" value={String(data.summary.totalCount)} tone="neutral" />
          <MetricCard icon={<TrendingUp className="h-4 w-4" />} label="总收入" value={formatCurrency(data.summary.totalIncome)} tone="income" />
          <MetricCard icon={<TrendingDown className="h-4 w-4" />} label="总支出" value={formatCurrency(data.summary.totalExpense)} tone="expense" />
          <MetricCard
            icon={<Wallet className="h-4 w-4" />}
            label="净现金流"
            value={formatCurrency(data.summary.netIncome)}
            tone={data.summary.netIncome >= 0 ? "income" : "expense"}
          />
        </div>

        <Card className="animate-slide-up overflow-hidden border-border/70">
          <CardContent className="pt-6">
            <SectionHeading title="月度趋势" description="按月观察收入、支出和净额变化" />
            <TrendChart trend={data.monthly} />
          </CardContent>
        </Card>

        <YearlySummaryTable rows={data.yearly} />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="animate-slide-up border-border/70">
            <CardHeader>
              <CardTitle className="text-xl">支出分类 Top 10</CardTitle>
              <CardDescription>高频花销结构一眼可见</CardDescription>
            </CardHeader>
            <CardContent>
              <BarList items={categoryItems} colorClass="bg-gradient-to-r from-chart-2 to-accent" emptyText="暂无分类支出数据" />
            </CardContent>
          </Card>

          <Card className="animate-slide-up border-border/70">
            <CardHeader>
              <CardTitle className="text-xl">对手方 Top 10</CardTitle>
              <CardDescription>主要支出去向与集中度</CardDescription>
            </CardHeader>
            <CardContent>
              <BarList items={counterpartyItems} colorClass="bg-gradient-to-r from-chart-4 to-chart-2" emptyText="暂无对手方数据" />
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <BreakdownTable
            title="账户贡献"
            description="按账户查看收入、支出与净额"
            rows={data.accounts.map((item) => ({ label: item.accountName, income: item.income, expense: item.expense }))}
          />
          <BreakdownTable
            title="来源贡献"
            description="按数据来源查看收支分布"
            rows={data.sources.map((item) => ({
              label: SOURCE_NAME_MAP[item.source] ?? item.source,
              income: item.income,
              expense: item.expense,
            }))}
          />
        </div>

        <Card className="animate-slide-up overflow-hidden border-border/70">
          <CardHeader>
            <CardTitle className="text-xl">支付宝综合分析</CardTitle>
            <CardDescription>独立查看支付宝账单的收支表现与消费结构</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard icon={<BarChart3 className="h-4 w-4" />} label="支付宝交易笔数" value={String(data.alipay.summary.totalCount)} tone="neutral" />
              <MetricCard icon={<TrendingUp className="h-4 w-4" />} label="支付宝总收入" value={formatCurrency(data.alipay.summary.totalIncome)} tone="income" />
              <MetricCard icon={<TrendingDown className="h-4 w-4" />} label="支付宝总支出" value={formatCurrency(data.alipay.summary.totalExpense)} tone="expense" />
              <MetricCard
                icon={<Wallet className="h-4 w-4" />}
                label="支付宝净现金流"
                value={formatCurrency(data.alipay.summary.netIncome)}
                tone={data.alipay.summary.netIncome >= 0 ? "income" : "expense"}
              />
            </div>

            <div>
              <SectionHeading title="支付宝月度趋势" description="按月查看支付宝收支和净额变化" />
              <TrendChart trend={data.alipay.monthly} />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card className="border-border/70">
                <CardHeader>
                  <CardTitle className="text-xl">支付宝支出分类 Top 10</CardTitle>
                  <CardDescription>支付宝消费类别集中度</CardDescription>
                </CardHeader>
                <CardContent>
                  <BarList items={alipayCategoryItems} colorClass="bg-gradient-to-r from-chart-1 to-chart-3" emptyText="暂无支付宝分类支出数据" />
                </CardContent>
              </Card>

              <Card className="border-border/70">
                <CardHeader>
                  <CardTitle className="text-xl">支付宝对手方 Top 10</CardTitle>
                  <CardDescription>支付宝主要支出去向</CardDescription>
                </CardHeader>
                <CardContent>
                  <BarList items={alipayCounterpartyItems} colorClass="bg-gradient-to-r from-chart-3 to-chart-2" emptyText="暂无支付宝对手方数据" />
                </CardContent>
              </Card>
            </div>

            <BreakdownTable
              title="支付宝账户贡献"
              description="按付款账户查看支付宝收支分布"
              rows={data.alipay.accounts.map((item) => ({
                label: item.accountName,
                income: item.income,
                expense: item.expense,
              }))}
            />
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <main className="min-h-screen bg-background">
      <AppShell title="分析报表" subtitle="趋势、结构与账户贡献" contentClassName="mx-auto max-w-7xl space-y-6 px-6 pb-16 pt-6">
        <Card className="animate-slide-up overflow-hidden border-border/70 bg-gradient-to-br from-primary/15 via-card to-accent/10">
          <CardContent className="pt-6">
            <form onSubmit={handleApply} className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_1fr_auto_auto]">
              <Input type="date" value={filters.startDate} onChange={(event) => updateFilter("startDate", event.target.value)} />
              <Input type="date" value={filters.endDate} onChange={(event) => updateFilter("endDate", event.target.value)} />
              <select
                value={filters.accountName}
                onChange={(event) => updateFilter("accountName", event.target.value)}
                className="h-10 rounded-xl border border-input bg-card/85 px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">全部账户</option>
                {accounts.map((account) => (
                  <option key={account} value={account}>
                    {account}
                  </option>
                ))}
              </select>
              <select
                value={filters.source}
                onChange={(event) => updateFilter("source", event.target.value)}
                className="h-10 rounded-xl border border-input bg-card/85 px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <Button type="submit" disabled={isLoading} className="shadow-sm">
                <BarChart3 className="mr-2 h-4 w-4" />
                应用筛选
              </Button>
              <Button type="button" variant="outline" onClick={handleReset} disabled={isLoading} className="bg-card/80">
                <RotateCcw className="mr-2 h-4 w-4" />
                重置
              </Button>
            </form>

            <div className="mt-3 flex flex-wrap gap-2">
              {[3, 6, 12].map((months) => (
                <Button
                  key={months}
                  type="button"
                  variant={isQuickRangeActive(months) ? "default" : "outline"}
                  onClick={() => handleQuickRange(months)}
                  disabled={isLoading}
                  className={isQuickRangeActive(months) ? "shadow-sm" : "bg-card/80"}
                >
                  最近 {months} 个月
                </Button>
              ))}
            </div>

            <p className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
              <Landmark className="h-3.5 w-3.5" />
              先设置筛选，再点击“应用筛选”；快捷按钮会直接更新数据。
            </p>
          </CardContent>
        </Card>

        {content}
      </AppShell>
    </main>
  );
}
