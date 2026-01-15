import type { EChartsOption } from "./types";

export type ChartIntentType = "monthly" | "daily" | "category" | "source";

export interface ChartIntent {
  type: ChartIntentType;
  onlyDirection?: "in" | "out";
}

export interface ChartTransaction {
  occurredAt: Date;
  amount: number;
  direction: string;
  category: string | null;
  source: string;
}

export function detectChartIntent(prompt: string): ChartIntent {
  const text = prompt.trim();
  const hasIncome = text.includes("收入");
  const hasExpense = text.includes("支出");
  const onlyDirection = hasIncome && !hasExpense ? "in" : hasExpense && !hasIncome ? "out" : undefined;

  if (text.includes("类别") || text.includes("分类") || text.includes("占比") || text.includes("饼图")) {
    return { type: "category", onlyDirection: "out" };
  }
  if (text.includes("来源") || text.includes("银行") || text.includes("渠道")) {
    return { type: "source" };
  }
  if (text.includes("每日") || text.includes("按日") || text.includes("日") && text.includes("趋势")) {
    return { type: "daily", onlyDirection };
  }
  if (text.includes("按月") || text.includes("月度") || text.includes("月份")) {
    return { type: "monthly", onlyDirection };
  }

  return { type: "monthly", onlyDirection };
}

export function buildChartOption(
  transactions: ChartTransaction[],
  intent: ChartIntent
): EChartsOption {
  switch (intent.type) {
    case "category":
      return buildCategoryPie(transactions);
    case "source":
      return buildSourceCompare(transactions);
    case "daily":
      return buildTimeTrend(transactions, "daily", intent.onlyDirection);
    case "monthly":
    default:
      return buildTimeTrend(transactions, "monthly", intent.onlyDirection);
  }
}

function formatLocalMonth(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function formatLocalDay(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildTimeTrend(
  transactions: ChartTransaction[],
  granularity: "monthly" | "daily",
  onlyDirection?: "in" | "out"
): EChartsOption {
  const stats = new Map<string, { income: number; expense: number }>();
  const formatter = granularity === "monthly" ? formatLocalMonth : formatLocalDay;

  for (const t of transactions) {
    if (onlyDirection && t.direction !== onlyDirection) {
      continue;
    }
    const key = formatter(t.occurredAt);
    const current = stats.get(key) || { income: 0, expense: 0 };
    if (t.direction === "in") {
      current.income += t.amount;
    } else {
      current.expense += t.amount;
    }
    stats.set(key, current);
  }

  const categories = Array.from(stats.keys()).sort();
  const incomeSeries = categories.map((key) => Number(stats.get(key)?.income.toFixed(2) || 0));
  const expenseSeries = categories.map((key) => Number(stats.get(key)?.expense.toFixed(2) || 0));

  const series: Array<{ name: string; type: string; data: number[]; smooth?: boolean }> = [];
  if (!onlyDirection || onlyDirection === "in") {
    series.push({ name: "收入", type: "line", data: incomeSeries, smooth: true });
  }
  if (!onlyDirection || onlyDirection === "out") {
    series.push({ name: "支出", type: "line", data: expenseSeries, smooth: true });
  }

  return {
    title: { text: granularity === "monthly" ? "月度收支趋势" : "每日收支趋势" },
    tooltip: { trigger: "axis" },
    legend: { data: series.map((s) => s.name) },
    xAxis: { type: "category", data: categories },
    yAxis: { type: "value" },
    series,
  };
}

function buildCategoryPie(transactions: ChartTransaction[]): EChartsOption {
  const stats = new Map<string, number>();

  for (const t of transactions) {
    if (t.direction !== "out") continue;
    const key = t.category?.trim() || "未分类";
    stats.set(key, (stats.get(key) || 0) + t.amount);
  }

  const data = Array.from(stats.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value: Number(value.toFixed(2)) }));

  if (data.length === 0) {
    throw new Error("没有可用的支出分类数据");
  }

  return {
    title: { text: "支出分类占比" },
    tooltip: { trigger: "item" },
    legend: { type: "scroll" },
    series: [
      {
        name: "支出分类",
        type: "pie",
        radius: "60%",
        data,
      },
    ],
  };
}

function buildSourceCompare(transactions: ChartTransaction[]): EChartsOption {
  const sourceNames: Record<string, string> = {
    alipay: "支付宝",
    ccb: "建设银行",
    cmb: "招商银行",
  };
  const stats = new Map<string, { income: number; expense: number }>();

  for (const t of transactions) {
    const key = sourceNames[t.source] || t.source;
    const current = stats.get(key) || { income: 0, expense: 0 };
    if (t.direction === "in") {
      current.income += t.amount;
    } else {
      current.expense += t.amount;
    }
    stats.set(key, current);
  }

  const categories = Array.from(stats.keys());
  const incomeSeries = categories.map((key) => Number(stats.get(key)?.income.toFixed(2) || 0));
  const expenseSeries = categories.map((key) => Number(stats.get(key)?.expense.toFixed(2) || 0));

  return {
    title: { text: "各来源收支对比" },
    tooltip: { trigger: "axis" },
    legend: { data: ["收入", "支出"] },
    xAxis: { type: "category", data: categories },
    yAxis: { type: "value" },
    series: [
      { name: "收入", type: "bar", data: incomeSeries },
      { name: "支出", type: "bar", data: expenseSeries },
    ],
  };
}
