import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import { applyUtcDateRangeFilter } from "@/lib/date-range";
import type { ApiResponse } from "@/lib/types";

const QueryParamsSchema = z.object({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  accountName: z.string().optional(),
  source: z.enum(["alipay", "ccb", "cmb"]).optional(),
});

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

function formatDateOutput(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getMonthKey(date: Date): string {
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  return `${date.getUTCFullYear()}-${month}`;
}

export async function GET(request: NextRequest): Promise<NextResponse<ApiResponse<AnalysisPayload>>> {
  try {
    const { searchParams } = new URL(request.url);
    const params = QueryParamsSchema.parse(Object.fromEntries(searchParams));

    const { startDate, endDate, accountName, source } = params;

    const baseWhere: Record<string, unknown> = {
      isDuplicate: false,
    };

    if (accountName) {
      baseWhere.accountName = accountName;
    }

    if (source) {
      baseWhere.source = source;
    }

    let appliedStart = startDate;
    let appliedEnd = endDate;

    if (!startDate || !endDate) {
      const rangeResult = await prisma.transaction.aggregate({
        where: baseWhere,
        _min: { occurredAt: true },
        _max: { occurredAt: true },
      });
      const minDate = rangeResult._min.occurredAt ?? null;
      const maxDate = rangeResult._max.occurredAt ?? null;
      if (minDate && maxDate) {
        appliedStart = appliedStart ?? formatDateOutput(minDate);
        appliedEnd = appliedEnd ?? formatDateOutput(maxDate);
      }
    }

    const where: Record<string, unknown> = { ...baseWhere };
    applyUtcDateRangeFilter(where, appliedStart, appliedEnd);

    const transactions = await prisma.transaction.findMany({
      where,
      select: {
        occurredAt: true,
        amount: true,
        direction: true,
        category: true,
        accountName: true,
        source: true,
        counterparty: true,
      },
    });

    const summary: Summary = {
      totalCount: 0,
      totalExpense: 0,
      totalIncome: 0,
      netIncome: 0,
    };

    const trendMap = new Map<string, TrendPoint>();
    const categoryMap = new Map<string, number>();
    const accountMap = new Map<string, { income: number; expense: number }>();
    const sourceMap = new Map<string, { income: number; expense: number }>();
    const counterpartyMap = new Map<string, number>();

    for (const transaction of transactions) {
      summary.totalCount += 1;

      const isIncome = transaction.direction === "in";
      if (isIncome) {
        summary.totalIncome += transaction.amount;
      } else {
        summary.totalExpense += transaction.amount;
      }

      const period = getMonthKey(transaction.occurredAt);
      const trendPoint = trendMap.get(period) ?? {
        period,
        income: 0,
        expense: 0,
        net: 0,
      };
      if (isIncome) {
        trendPoint.income += transaction.amount;
      } else {
        trendPoint.expense += transaction.amount;
      }
      trendPoint.net = trendPoint.income - trendPoint.expense;
      trendMap.set(period, trendPoint);

      const accountKey = transaction.accountName?.trim() || "未知帐号";
      const accountBucket = accountMap.get(accountKey) ?? { income: 0, expense: 0 };
      if (isIncome) {
        accountBucket.income += transaction.amount;
      } else {
        accountBucket.expense += transaction.amount;
      }
      accountMap.set(accountKey, accountBucket);

      const sourceKey = transaction.source;
      const sourceBucket = sourceMap.get(sourceKey) ?? { income: 0, expense: 0 };
      if (isIncome) {
        sourceBucket.income += transaction.amount;
      } else {
        sourceBucket.expense += transaction.amount;
      }
      sourceMap.set(sourceKey, sourceBucket);

      if (!isIncome) {
        const categoryKey = transaction.category?.trim() || "未分类";
        categoryMap.set(categoryKey, (categoryMap.get(categoryKey) ?? 0) + transaction.amount);

        const counterpartyKey = transaction.counterparty?.trim() || "未指定";
        counterpartyMap.set(counterpartyKey, (counterpartyMap.get(counterpartyKey) ?? 0) + transaction.amount);
      }
    }

    summary.netIncome = summary.totalIncome - summary.totalExpense;

    const trend = Array.from(trendMap.values()).sort((a, b) => a.period.localeCompare(b.period));

    const categories = Array.from(categoryMap.entries())
      .map(([category, amount]) => ({ category, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 10);

    const accounts = Array.from(accountMap.entries())
      .map(([accountName, values]) => ({ accountName, ...values }))
      .sort((a, b) => (b.expense + b.income) - (a.expense + a.income));

    const sources = Array.from(sourceMap.entries())
      .map(([sourceName, values]) => ({ source: sourceName, ...values }))
      .sort((a, b) => (b.expense + b.income) - (a.expense + a.income));

    const counterparties = Array.from(counterpartyMap.entries())
      .map(([counterparty, amount]) => ({ counterparty, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 10);

    return NextResponse.json({
      success: true,
      data: {
        summary,
        trend,
        categories,
        accounts,
        sources,
        counterparties,
        dateRange: appliedStart && appliedEnd ? { start: appliedStart, end: appliedEnd } : null,
      },
    });
  } catch (error) {
    console.error("分析统计失败:", error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: `参数格式错误: ${error.errors[0]?.message}` },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "统计失败" },
      { status: 500 }
    );
  }
}
