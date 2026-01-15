import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import { EChartsOptionSchema } from "@/lib/types";
import type { ApiResponse } from "@/lib/types";

const SaveRequestSchema = z.object({
  title: z.string().max(100).optional(),
  prompt: z.string().max(500).optional(),
  option: EChartsOptionSchema,
  dataFilter: z.object({
    startDate: z.string().optional(),
    endDate: z.string().optional(),
    source: z.enum(["alipay", "ccb", "cmb"]).optional(),
  }).optional(),
});

interface SaveResult {
  id: string;
}

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<SaveResult>>> {
  try {
    const body = await request.json();
    const { title, prompt, option, dataFilter } = SaveRequestSchema.parse(body);

    const chartRequest = await prisma.chartRequest.create({
      data: {
        prompt: title || prompt || "已保存图表",
        dataFilter: JSON.stringify({
          ...dataFilter,
          kind: "user",
        }),
        optionJson: JSON.stringify(option),
      },
    });

    return NextResponse.json({
      success: true,
      data: { id: chartRequest.id },
    });
  } catch (error) {
    console.error("保存图表失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "保存图表失败" },
      { status: 500 }
    );
  }
}
