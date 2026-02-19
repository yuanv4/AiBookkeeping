import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import prisma from "@/lib/db";
import { applyCrossSourceDeduplication } from "@/lib/dedupe";
import type { Prisma } from "@/generated/prisma/client";
import type { ApiResponse } from "@/lib/types";

// 单条交易 Schema（后端二次校验）
const TransactionDraftSchema = z.object({
  occurredAt: z.string().transform((s) => {
    const date = new Date(s);
    if (isNaN(date.getTime())) throw new Error("无效日期");
    return date;
  }),
  amount: z.number().positive("金额必须为正数").max(100_000_000, "金额超出合理范围"),
  direction: z.enum(["in", "out"]),
  currency: z.string().max(10).default("CNY"),
  counterparty: z.string().max(200).nullable(),
  description: z.string().max(500).nullable(),
  category: z.string().max(100).nullable(),
  accountName: z.string().max(100).nullable(),
  source: z.enum(["alipay", "ccb", "cmb", "spdb"]),
  sourceRaw: z.string().max(5000), // 限制原始数据大小
  sourceRowId: z.string().max(200),
  balance: z.number().min(-100_000_000).max(100_000_000).nullable(),
  status: z.string().max(100).nullable(),
  counterpartyAccount: z.string().max(200).nullable(),
  transactionId: z.string().max(200).nullable(),
  merchantOrderId: z.string().max(200).nullable(),
  memo: z.string().max(500).nullable(),
  cashRemit: z.string().max(20).nullable(),
});

type TransactionDraft = z.infer<typeof TransactionDraftSchema>;

// 请求体 Schema
const CommitRequestSchema = z.object({
  fileName: z.string().max(255),
  fileSize: z.number().int().positive().max(10 * 1024 * 1024), // 最大 10MB
  source: z.enum(["alipay", "ccb", "cmb", "spdb"]),
  sourceType: z.enum(["csv", "xls", "pdf"]),
  drafts: z.array(TransactionDraftSchema).max(5000), // 最多 5000 条
  warningCount: z.number().int().min(0).default(0),
});

interface CommitResult {
  batchId: string;
  rowCount: number;
  skippedCount: number; // 跳过的重复记录数
}

// 分批大小
const BATCH_SIZE = 100;

function buildTransactionData(
  draft: TransactionDraft,
  batchId: string
): Prisma.TransactionCreateManyInput {
  return {
    occurredAt: draft.occurredAt,
    amount: draft.amount,
    direction: draft.direction,
    currency: draft.currency,
    counterparty: draft.counterparty,
    description: draft.description,
    category: draft.category,
    accountName: draft.accountName,
    source: draft.source,
    sourceRaw: draft.sourceRaw,
    sourceRowId: draft.sourceRowId,
    importBatchId: batchId,
    balance: draft.balance,
    status: draft.status,
    counterpartyAccount: draft.counterpartyAccount,
    transactionId: draft.transactionId,
    merchantOrderId: draft.merchantOrderId,
    memo: draft.memo,
    cashRemit: draft.cashRemit,
  };
}

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<CommitResult>>> {
  try {
    const body = await request.json();
    const validatedData = CommitRequestSchema.parse(body);

    const { fileName, fileSize, source, sourceType, drafts, warningCount } = validatedData;

    // 检查来源一致性（防止伪造）
    const inconsistentSource = drafts.find((d) => d.source !== source);
    if (inconsistentSource) {
      return NextResponse.json(
        { success: false, error: "交易来源与文件来源不一致" },
        { status: 400 }
      );
    }

    // 1. 先创建导入批次
    const batch = await prisma.importBatch.create({
      data: {
        fileName,
        fileSize,
        source,
        sourceType,
        rowCount: 0, // 先设为 0，后面更新
        warningCount,
      },
    });

    // 2. 先查询已存在的记录（基于 source + sourceRowId 唯一约束）
    // SQLite 参数限制，需要分批查询
    const existingSet = new Set<string>();
    const sourceRowIds = drafts.map((d) => d.sourceRowId);
    
    for (let i = 0; i < sourceRowIds.length; i += BATCH_SIZE) {
      const batchIds = sourceRowIds.slice(i, i + BATCH_SIZE);
      const existingRecords = await prisma.transaction.findMany({
        where: {
          source: source,
          sourceRowId: { in: batchIds },
        },
        select: { sourceRowId: true },
      });
      existingRecords.forEach((r) => existingSet.add(r.sourceRowId));
    }
    
    // 过滤掉已存在的记录
    const newDrafts = drafts.filter((d) => !existingSet.has(d.sourceRowId));
    const skippedCount = drafts.length - newDrafts.length;
    
    // 3. 分批插入新交易记录
    let insertedCount = 0;

    for (let i = 0; i < newDrafts.length; i += BATCH_SIZE) {
      const batchDrafts = newDrafts.slice(i, i + BATCH_SIZE);

      try {
        const result = await prisma.transaction.createMany({
          data: batchDrafts.map((draft) => buildTransactionData(draft, batch.id)),
        });

        insertedCount += result.count;
      } catch (batchError) {
        console.error(`批次 ${i / BATCH_SIZE + 1} 插入失败:`, batchError);
        // 单条插入重试，以确保尽可能多的数据入库
        for (const draft of batchDrafts) {
          try {
            await prisma.transaction.create({
              data: buildTransactionData(draft, batch.id),
            });
            insertedCount++;
          } catch {
            // 忽略单条插入失败（可能是重复）
          }
        }
      }
    }

    // 4. 更新批次的实际行数
    await prisma.importBatch.update({
      where: { id: batch.id },
      data: { rowCount: insertedCount },
    });

    // 如果没有任何记录被插入，删除批次
    if (insertedCount === 0) {
      await prisma.importBatch.delete({ where: { id: batch.id } });
      return NextResponse.json({
        success: true,
        data: {
          batchId: "",
          rowCount: 0,
          skippedCount: drafts.length,
        },
      });
    }

    const insertedTransactions = await prisma.transaction.findMany({
      where: { importBatchId: batch.id },
      select: {
        occurredAt: true,
        amount: true,
        direction: true,
        counterparty: true,
      },
    });

    await applyCrossSourceDeduplication(prisma, insertedTransactions);

    return NextResponse.json({
      success: true,
      data: {
        batchId: batch.id,
        rowCount: insertedCount,
        skippedCount,
      },
    });
  } catch (error) {
    console.error("导入数据失败:", error);
    console.error("Error stack:", (error as Error).stack);

    if (error instanceof z.ZodError) {
      const firstError = error.errors[0];
      return NextResponse.json(
        { success: false, error: `数据格式错误: ${firstError?.path.join(".")} - ${firstError?.message}` },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "导入数据失败" },
      { status: 500 }
    );
  }
}
