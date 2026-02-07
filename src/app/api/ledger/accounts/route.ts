import { NextResponse } from "next/server";
import prisma from "@/lib/db";
import type { ApiResponse } from "@/lib/types";

export async function GET(): Promise<NextResponse<ApiResponse<string[]>>> {
  try {
    const records = await prisma.transaction.findMany({
      where: {
        isDuplicate: false,
        accountName: { not: null },
      },
      select: { accountName: true },
      distinct: ["accountName"],
    });

    const accounts = Array.from(
      new Set(
        records
          .map((record) => record.accountName?.trim() || "")
          .filter((name) => name.length > 0)
      )
    ).sort((a, b) => a.localeCompare(b, "zh-CN"));

    return NextResponse.json({
      success: true,
      data: accounts,
    });
  } catch (error) {
    console.error("获取帐号列表失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "查询失败" },
      { status: 500 }
    );
  }
}
