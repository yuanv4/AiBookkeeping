import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import { buildChartOption } from "@/lib/charts";
import type { ApiResponse } from "@/lib/types";

const SeedRequestSchema = z.object({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  source: z.enum(["alipay", "ccb", "cmb"]).optional(),
});

interface SeedResult {
  created: number;
}

const PRESET_DEFINITIONS = [
  { title: "月度收支趋势", intent: { type: "monthly" as const } },
  { title: "支出分类占比", intent: { type: "category" as const } },
  { title: "来源收支对比", intent: { type: "source" as const } },
];

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<SeedResult>>> {
  try {
    const body = await request.json();
    const params = SeedRequestSchema.parse(body);

    const where: Record<string, unknown> = {};
    if (params.startDate || params.endDate) {
      where.occurredAt = {};
      if (params.startDate) {
        (where.occurredAt as Record<string, Date>).gte = new Date(params.startDate);
      }
      if (params.endDate) {
        (where.occurredAt as Record<string, Date>).lte = new Date(params.endDate);
      }
    }
    if (params.source) {
      where.source = params.source;
    }

    const totalCount = await prisma.transaction.count({ where });
    if (totalCount === 0) {
      return NextResponse.json({ success: true, data: { created: 0 } });
    }

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

    const systemTitles = PRESET_DEFINITIONS.map((item) => `系统示例：${item.title}`);
    const existing = await prisma.chartRequest.findMany({
      where: {
        prompt: { in: systemTitles },
      },
      select: { prompt: true },
    });
    const existingSet = new Set(existing.map((item) => item.prompt));

    const createdData = PRESET_DEFINITIONS.filter((item) => !existingSet.has(`系统示例：${item.title}`))
      .flatMap((item) => {
        try {
          const option = buildChartOption(transactions, item.intent);
          return [{
            prompt: `系统示例：${item.title}`,
            dataFilter: JSON.stringify({
              ...params,
              kind: "system",
            }),
            optionJson: JSON.stringify(option),
          }];
        } catch {
          return [];
        }
      });

    if (createdData.length > 0) {
      await prisma.chartRequest.createMany({ data: createdData });
    }

    return NextResponse.json({
      success: true,
      data: { created: createdData.length },
    });
  } catch (error) {
    console.error("初始化系统示例失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "初始化系统示例失败" },
      { status: 500 }
    );
  }
}
