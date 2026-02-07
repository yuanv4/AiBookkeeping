import { NextResponse } from "next/server";
import prisma from "@/lib/db";
import type { ApiResponse } from "@/lib/types";

interface Stats {
  totalCount: number;
  totalExpense: number;
  totalIncome: number;
  netIncome: number;
}

export async function GET(): Promise<NextResponse<ApiResponse<Stats>>> {
  try {
    // 统计总笔数
    const totalCount = await prisma.transaction.count({
      where: { isDuplicate: false },
    });

    // 统计支出
    const expenseResult = await prisma.transaction.aggregate({
      where: { direction: "out", isDuplicate: false },
      _sum: { amount: true },
    });

    // 统计收入
    const incomeResult = await prisma.transaction.aggregate({
      where: { direction: "in", isDuplicate: false },
      _sum: { amount: true },
    });

    const totalExpense = expenseResult._sum.amount || 0;
    const totalIncome = incomeResult._sum.amount || 0;

    return NextResponse.json({
      success: true,
      data: {
        totalCount,
        totalExpense,
        totalIncome,
        netIncome: totalIncome - totalExpense,
      },
    });
  } catch (error) {
    console.error("统计失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "统计失败" },
      { status: 500 }
    );
  }
}
