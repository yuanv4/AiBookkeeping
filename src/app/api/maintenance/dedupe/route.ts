import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import { applyCrossSourceDeduplication } from "@/lib/dedupe";
import type { ApiResponse } from "@/lib/types";

const DedupeRequestSchema = z.object({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
});

interface DedupeResult {
  candidateCount: number;
  processedGroups: number;
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
    occurredAt.lte = new Date(endDate);
  }
  where.occurredAt = occurredAt;
}

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<DedupeResult>>> {
  try {
    const body = await request.json().catch(() => ({}));
    const { startDate, endDate } = DedupeRequestSchema.parse(body);

    const where: Record<string, unknown> = {};
    applyDateRangeFilter(where, startDate, endDate);

    const candidates = await prisma.transaction.findMany({
      where,
      select: {
        occurredAt: true,
        amount: true,
        direction: true,
        counterparty: true,
      },
    });

    const MAX_CANDIDATES = 100_000;
    if (candidates.length > MAX_CANDIDATES) {
      return NextResponse.json(
        { success: false, error: "候选数据量过大，请缩小日期范围" },
        { status: 400 }
      );
    }

    const processedGroups = await applyCrossSourceDeduplication(prisma, candidates);

    return NextResponse.json({
      success: true,
      data: {
        candidateCount: candidates.length,
        processedGroups,
      },
    });
  } catch (error) {
    console.error("重复检测失败:", error);
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: `参数格式错误: ${error.errors[0]?.message}` },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "重复检测失败" },
      { status: 500 }
    );
  }
}
