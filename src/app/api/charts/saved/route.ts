import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/db";
import type { ApiResponse, EChartsOption } from "@/lib/types";

interface SavedChart {
  id: string;
  title: string;
  option: EChartsOption;
  createdAt: string;
  kind: "system" | "user";
  dataFilter: Record<string, unknown> | null;
}

export async function GET(_request: NextRequest): Promise<NextResponse<ApiResponse<SavedChart[]>>> {
  try {
    const records = await prisma.chartRequest.findMany({
      orderBy: { createdAt: "desc" },
      take: 50,
    });

    const results: SavedChart[] = [];

    for (const record of records) {
      let option: EChartsOption | null = null;
      try {
        option = JSON.parse(record.optionJson) as EChartsOption;
      } catch {
        option = null;
      }

      if (!option) {
        continue;
      }

      let dataFilter: Record<string, unknown> | null = null;
      let kind: "system" | "user" = "user";

      if (record.dataFilter) {
        try {
          dataFilter = JSON.parse(record.dataFilter) as Record<string, unknown>;
          if (dataFilter.kind === "system") {
            kind = "system";
          }
        } catch {
          dataFilter = null;
        }
      }

      results.push({
        id: record.id,
        title: record.prompt,
        option,
        createdAt: record.createdAt.toISOString(),
        kind,
        dataFilter,
      });
    }

    return NextResponse.json({
      success: true,
      data: results,
    });
  } catch (error) {
    console.error("获取已保存图表失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "获取已保存图表失败" },
      { status: 500 }
    );
  }
}
