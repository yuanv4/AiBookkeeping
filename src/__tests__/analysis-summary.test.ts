/**
 * 分析汇总 API 集成测试
 *
 * 运行测试：
 * npm test -- analysis-summary.test.ts
 *
 * 前置条件：
 * 1. 启动本地服务（默认 http://localhost:3000，可用 BASE_URL 覆盖）
 */

import { describe, expect, test } from "vitest";

const DEFAULT_BASE_URL = "http://localhost:3000";

type AnalysisResponse = {
  success: boolean;
  data?: {
    summary: {
      totalCount: number;
      totalExpense: number;
      totalIncome: number;
      netIncome: number;
    };
    trend: { period: string }[];
    categories: unknown[];
    accounts: unknown[];
    sources: unknown[];
    counterparties: unknown[];
    dateRange: { start: string; end: string } | null;
  };
  error?: string;
};

function normalizeBaseUrl(rawBaseUrl?: string): string {
  if (!rawBaseUrl || rawBaseUrl === "/") {
    return DEFAULT_BASE_URL;
  }

  if (rawBaseUrl.startsWith("//")) {
    return `http:${rawBaseUrl}`;
  }

  if (!/^https?:\/\//i.test(rawBaseUrl)) {
    return `http://${rawBaseUrl.replace(/^\/+/, "")}`;
  }

  return rawBaseUrl.replace(/\/+$/, "");
}

const BASE_URL = normalizeBaseUrl(process.env.BASE_URL);

function toPeriod(date: string): string {
  const [year, month] = date.split("-");
  return `${year}-${month}`;
}

async function requestSummary(params?: Record<string, string>): Promise<AnalysisResponse> {
  const url = new URL(`${BASE_URL}/api/analysis/summary`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
  }
  const response = await fetch(url.toString());
  expect(response.status).toBe(200);
  return (await response.json()) as AnalysisResponse;
}

describe("分析汇总 API 集成测试", () => {
  test("返回结构完整", async () => {
    const result = await requestSummary();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    if (!result.data) return;
    expect(typeof result.data.summary.totalCount).toBe("number");
    expect(typeof result.data.summary.totalExpense).toBe("number");
    expect(typeof result.data.summary.totalIncome).toBe("number");
    expect(typeof result.data.summary.netIncome).toBe("number");
    expect(Array.isArray(result.data.trend)).toBe(true);
  });

  test("日期范围按本地日历天计算", async () => {
    const startDate = "2024-01-01";
    const endDate = "2024-12-31";
    const result = await requestSummary({ startDate, endDate });

    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    if (!result.data) return;

    expect(result.data.dateRange).toEqual({ start: startDate, end: endDate });

    const startPeriod = toPeriod(startDate);
    const endPeriod = toPeriod(endDate);
    for (const point of result.data.trend) {
      expect(point.period >= startPeriod).toBe(true);
      expect(point.period <= endPeriod).toBe(true);
    }
  });

  test("日期范围使用 UTC 日界限", async () => {
    const startDate = "2024-06-30";
    const endDate = "2024-07-01";
    const result = await requestSummary({ startDate, endDate });

    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    if (!result.data) return;

    expect(result.data.dateRange).toEqual({ start: startDate, end: endDate });

    const startPeriod = toPeriod(startDate);
    const endPeriod = toPeriod(endDate);
    for (const point of result.data.trend) {
      expect(point.period >= startPeriod).toBe(true);
      expect(point.period <= endPeriod).toBe(true);
    }
  });
});
