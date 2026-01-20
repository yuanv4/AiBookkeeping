import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import type { ApiResponse, PaginatedResult } from "@/lib/types";

// 查询参数 Schema
const QueryParamsSchema = z.object({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  accountName: z.string().optional(),
  direction: z.enum(["in", "out"]).optional(),
  keyword: z.string().optional(),
  page: z.coerce.number().min(1).default(1),
  pageSize: z.coerce.number().min(1).max(100).default(20),
});

interface TransactionWithBatch {
  id: string;
  occurredAt: Date;
  amount: number;
  direction: string;
  currency: string;
  counterparty: string | null;
  description: string | null;
  category: string | null;
  accountName: string | null;
  source: string;
  sourceRowId: string;
  createdAt: Date;
  importBatch: {
    fileName: string;
  };
}

function applyDateRangeFilter(
  where: Record<string, unknown>,
  startDate?: string,
  endDate?: string
): void {
  if (!startDate && !endDate) return;
  const occurredAt: Record<string, Date> = {};
  if (startDate) {
    occurredAt.gte = new Date(startDate);
  }
  if (endDate) {
    const end = new Date(endDate);
    end.setDate(end.getDate() + 1);
    occurredAt.lt = end;
  }
  where.occurredAt = occurredAt;
}

export async function GET(request: NextRequest): Promise<NextResponse<ApiResponse<PaginatedResult<TransactionWithBatch>>>> {
  try {
    const { searchParams } = new URL(request.url);
    const params = QueryParamsSchema.parse(Object.fromEntries(searchParams));

    const { startDate, endDate, accountName, direction, keyword, page, pageSize } = params;

    // 构建查询条件
    const where: Record<string, unknown> = {
      isDuplicate: false,
    };

    applyDateRangeFilter(where, startDate, endDate);

    if (accountName) {
      where.accountName = accountName;
    }

    if (direction) {
      where.direction = direction;
    }

    if (keyword) {
      const orConditions: Record<string, unknown>[] = [
        { counterparty: { contains: keyword } },
        { description: { contains: keyword } },
        { category: { contains: keyword } },
        { accountName: { contains: keyword } },
        { source: { contains: keyword } },
      ];

      const amountValue = Number.parseFloat(keyword.replace(/[,，\s]/g, ""));
      if (!Number.isNaN(amountValue)) {
        orConditions.push({ amount: amountValue });
      }

      if (keyword.includes("支付宝") || keyword.toLowerCase().includes("alipay")) {
        orConditions.push({ source: "alipay" });
      }
      if (keyword.includes("建设银行") || keyword.includes("建行") || keyword.toLowerCase().includes("ccb")) {
        orConditions.push({ source: "ccb" });
      }
      if (keyword.includes("招商银行") || keyword.includes("招行") || keyword.toLowerCase().includes("cmb")) {
        orConditions.push({ source: "cmb" });
      }

      where.OR = orConditions;
    }

    // 查询总数
    const total = await prisma.transaction.count({ where });

    // 分页查询
    const transactions = await prisma.transaction.findMany({
      where,
      orderBy: { occurredAt: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
      include: {
        importBatch: {
          select: {
            fileName: true,
          },
        },
      },
    });

    return NextResponse.json({
      success: true,
      data: {
        data: transactions,
        total,
        page,
        pageSize,
        totalPages: Math.ceil(total / pageSize),
      },
    });
  } catch (error) {
    console.error("查询交易记录失败:", error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: `参数格式错误: ${error.errors[0]?.message}` },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "查询失败" },
      { status: 500 }
    );
  }
}
