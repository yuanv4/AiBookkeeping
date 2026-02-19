import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import { applyUtcDateRangeFilter } from "@/lib/date-range";

const QueryParamsSchema = z.object({
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  accountName: z.string().optional(),
  direction: z.enum(["in", "out"]).optional(),
  keyword: z.string().optional(),
});

function escapeCsvValue(value: string | number | null): string {
  if (value == null) return "";
  const raw = String(value);
  if (/[",\n\r]/.test(raw)) {
    return `"${raw.replace(/"/g, '""')}"`;
  }
  return raw;
}

function formatDate(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  const second = String(date.getUTCSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function buildFileName(): string {
  const now = new Date();
  const ts = formatDate(now).replace(/[-:\s]/g, "");
  return `ledger-export-${ts}.csv`;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const { searchParams } = new URL(request.url);
    const params = QueryParamsSchema.parse(Object.fromEntries(searchParams));
    const { startDate, endDate, accountName, direction, keyword } = params;

    const where: Record<string, unknown> = {
      isDuplicate: false,
    };

    applyUtcDateRangeFilter(where, startDate, endDate);

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
      if (
        keyword.includes("浦发银行") ||
        keyword.includes("浦东发展银行") ||
        keyword.toLowerCase().includes("spdb")
      ) {
        orConditions.push({ source: "spdb" });
      }

      where.OR = orConditions;
    }

    const transactions = await prisma.transaction.findMany({
      where,
      orderBy: { occurredAt: "desc" },
      select: {
        occurredAt: true,
        amount: true,
        direction: true,
        currency: true,
        counterparty: true,
        description: true,
        category: true,
        accountName: true,
        source: true,
        balance: true,
        status: true,
        counterpartyAccount: true,
        transactionId: true,
        merchantOrderId: true,
        memo: true,
        cashRemit: true,
        sourceRowId: true,
      },
    });

    const headers = [
      "occurredAt",
      "amount",
      "direction",
      "currency",
      "counterparty",
      "description",
      "category",
      "accountName",
      "source",
      "balance",
      "status",
      "counterpartyAccount",
      "transactionId",
      "merchantOrderId",
      "memo",
      "cashRemit",
      "sourceRowId",
    ];

    const lines: string[] = [];
    lines.push(headers.join(","));

    for (const tx of transactions) {
      const row = [
        formatDate(tx.occurredAt),
        tx.amount,
        tx.direction,
        tx.currency,
        tx.counterparty,
        tx.description,
        tx.category,
        tx.accountName,
        tx.source,
        tx.balance,
        tx.status,
        tx.counterpartyAccount,
        tx.transactionId,
        tx.merchantOrderId,
        tx.memo,
        tx.cashRemit,
        tx.sourceRowId,
      ].map(escapeCsvValue);
      lines.push(row.join(","));
    }

    const csvContent = lines.join("\n");
    const fileName = buildFileName();

    return new NextResponse(csvContent, {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="${fileName}"`,
      },
    });
  } catch (error) {
    console.error("导出 CSV 失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "导出失败" },
      { status: 500 }
    );
  }
}
