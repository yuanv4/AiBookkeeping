import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/db";
import { buildChartOption, detectChartIntent } from "@/lib/charts";
import { ChartGenerateRequestSchema, EChartsOptionSchema } from "@/lib/types";
import type { ApiResponse, EChartsOption } from "@/lib/types";

interface ChartGenerateResult {
  option: EChartsOption;
  requestId: string;
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

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<ChartGenerateResult>>> {
  try {
    const body = await request.json();
    const { prompt, startDate, endDate, source } = ChartGenerateRequestSchema.parse(body);

    // 构建查询条件
    const where: Record<string, unknown> = {
      isDuplicate: false,
    };

    applyDateRangeFilter(where, startDate, endDate);
    
    if (source) {
      where.source = source;
    }

    // 先统计总量，避免超大数据集导致接口阻塞
    const totalCount = await prisma.transaction.count({ where });

    if (totalCount === 0) {
      return NextResponse.json(
        { success: false, error: "没有找到符合条件的交易数据" },
        { status: 400 }
      );
    }

    const MAX_CHART_ROWS = 50000;
    if (totalCount > MAX_CHART_ROWS) {
      return NextResponse.json(
        { success: false, error: "数据量过大，请缩小日期范围或筛选条件" },
        { status: 400 }
      );
    }

    // 获取交易数据（全量，不采样）
    const transactions = await prisma.transaction.findMany({
      where,
      orderBy: { occurredAt: "asc" },
      select: {
        occurredAt: true,
        amount: true,
        direction: true,
        category: true,
        source: true,
      },
    });

    const intent = detectChartIntent(prompt);
    const rawOption = buildChartOption(transactions, intent);

    // 校验 option
    const validatedOption = EChartsOptionSchema.parse(rawOption);

    // 保存请求记录
    const chartRequest = await prisma.chartRequest.create({
      data: {
        prompt,
        dataFilter: JSON.stringify({ startDate, endDate, source, kind: "user" }),
        optionJson: JSON.stringify(validatedOption),
      },
    });

    return NextResponse.json({
      success: true,
      data: {
        option: validatedOption,
        requestId: chartRequest.id,
      },
    });
  } catch (error) {
    console.error("生成图表失败:", error);

    const message = error instanceof Error ? error.message : "生成图表失败";
    const status = message.includes("没有可用的支出分类数据") ? 400 : 500;

    return NextResponse.json(
      { success: false, error: message },
      { status }
    );
  }
}
