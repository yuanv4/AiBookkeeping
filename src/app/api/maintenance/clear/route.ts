import { NextResponse } from "next/server";
import prisma from "@/lib/db";
import type { ApiResponse } from "@/lib/types";

interface ClearResult {
  deletedTransactions: number;
  deletedBatches: number;
}

export async function POST(): Promise<NextResponse<ApiResponse<ClearResult>>> {
  try {
    const [transactions, batches] = await prisma.$transaction([
      prisma.transaction.deleteMany(),
      prisma.importBatch.deleteMany(),
    ]);

    return NextResponse.json({
      success: true,
      data: {
        deletedTransactions: transactions.count,
        deletedBatches: batches.count,
      },
    });
  } catch (error) {
    console.error("清空数据失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "清空失败" },
      { status: 500 }
    );
  }
}
