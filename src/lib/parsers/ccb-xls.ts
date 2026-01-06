import * as XLSX from "xlsx";
import type { UnifiedTransactionDraft, ParseWarning, ParseResult } from "../types";

/**
 * 建设银行 XLS 列名映射
 */
const CCB_COLUMN_ALIASES: Record<string, string[]> = {
  index: ["序号"],
  summary: ["摘要"],
  currency: ["币别"],
  cashRemit: ["钞汇"], // 钞/汇
  date: ["交易日期"],
  amount: ["交易金额"],
  balance: ["账户余额"],
  location: ["交易地点/附言", "交易地点", "附言"],
  counterparty: ["对方账号与户名", "对方账号", "对方户名"],
};

/**
 * 查找标题行
 */
function findHeaderRow(
  data: unknown[][]
): { rowIndex: number; columnMap: Record<string, number> } | null {
  for (let i = 0; i < Math.min(data.length, 10); i++) {
    const row = data[i];
    if (!Array.isArray(row)) continue;

    const rowStr = row.map((c) => String(c || "").trim());

    // 检查是否包含关键列名
    if (
      rowStr.some((c) => c.includes("交易日期")) &&
      rowStr.some((c) => c.includes("交易金额"))
    ) {
      const columnMap: Record<string, number> = {};

      for (let j = 0; j < rowStr.length; j++) {
        const cell = rowStr[j];
        for (const [key, aliases] of Object.entries(CCB_COLUMN_ALIASES)) {
          if (aliases.some((alias) => cell.includes(alias))) {
            columnMap[key] = j;
            break;
          }
        }
      }

      return { rowIndex: i, columnMap };
    }
  }

  return null;
}

/**
 * 解析日期 (YYYYMMDD 格式)
 */
function parseDate(value: unknown): Date | null {
  if (!value) return null;

  const str = String(value).trim();

  // YYYYMMDD 格式
  if (/^\d{8}$/.test(str)) {
    const year = parseInt(str.substring(0, 4));
    const month = parseInt(str.substring(4, 6)) - 1;
    const day = parseInt(str.substring(6, 8));
    return new Date(year, month, day);
  }

  // 尝试其他格式
  const date = new Date(str);
  return isNaN(date.getTime()) ? null : date;
}

/**
 * 解析金额
 */
function parseAmount(value: unknown): { amount: number; direction: "in" | "out" } | null {
  if (value === null || value === undefined) return null;

  let num: number;
  if (typeof value === "number") {
    num = value;
  } else {
    const str = String(value).replace(/[,，\s]/g, "");
    num = parseFloat(str);
  }

  if (isNaN(num) || num === 0) return null;

  return {
    amount: Math.abs(num),
    direction: num > 0 ? "in" : "out",
  };
}

/**
 * 解析对方信息
 */
function parseCounterparty(value: unknown): { account: string | null; name: string | null } {
  if (!value) return { account: null, name: null };

  const str = String(value).trim();

  // 格式: 账号/户名
  if (str.includes("/")) {
    const [account, name] = str.split("/");
    return {
      account: account?.trim() || null,
      name: name?.trim() || null,
    };
  }

  return { account: null, name: str };
}

/**
 * 解析余额
 */
function parseBalance(value: unknown): number | null {
  if (value === null || value === undefined) return null;

  let num: number;
  if (typeof value === "number") {
    num = value;
  } else {
    const str = String(value).replace(/[,，\s]/g, "");
    num = parseFloat(str);
  }

  return isNaN(num) ? null : num;
}

/**
 * 建设银行 XLS 解析器
 */
export async function parseCcbXls(buffer: ArrayBuffer): Promise<ParseResult> {
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  // 转换为二维数组
  const data = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    blankrows: false,
  }) as unknown[][];

  // 查找标题行
  const headerInfo = findHeaderRow(data);
  if (!headerInfo) {
    throw new Error("无法找到标题行，请确认文件格式正确");
  }

  const { rowIndex: headerRowIndex, columnMap } = headerInfo;

  // 检查必要列
  if (columnMap.date === undefined || columnMap.amount === undefined) {
    throw new Error("缺少必要列：交易日期或交易金额");
  }

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];

  // 解析数据行
  for (let i = headerRowIndex + 1; i < data.length; i++) {
    const row = data[i];
    if (!Array.isArray(row) || row.length === 0) continue;

    const rowNum = i + 1;
    const rawRow: Record<string, unknown> = {};

    // 提取原始数据
    for (const [key, colIndex] of Object.entries(columnMap)) {
      rawRow[key] = row[colIndex];
    }

    // 解析日期
    const occurredAt = parseDate(rawRow.date);
    if (!occurredAt) {
      warnings.push({
        row: rowNum,
        field: "date",
        message: `无效的交易日期: ${rawRow.date}`,
      });
      continue;
    }

    // 解析金额
    const amountInfo = parseAmount(rawRow.amount);
    if (!amountInfo) {
      // 跳过金额为0的记录
      continue;
    }

    // 解析对方信息
    const counterpartyInfo = parseCounterparty(rawRow.counterparty);

    // 解析余额
    const balance = parseBalance(rawRow.balance);

    // 生成行 ID
    const index = rawRow.index ? String(rawRow.index) : String(i - headerRowIndex);
    const sourceRowId = `ccb-${index}-${occurredAt.getTime()}`;

    drafts.push({
      occurredAt,
      amount: amountInfo.amount,
      direction: amountInfo.direction,
      currency: "CNY",
      counterparty: counterpartyInfo.name,
      description: rawRow.location ? String(rawRow.location).trim() : null,
      category: rawRow.summary ? String(rawRow.summary).trim() : null,
      accountName: "建设银行",
      source: "ccb",
      sourceRaw: JSON.stringify(rawRow),
      sourceRowId,
      
      // ===== 扩展字段 =====
      balance, // 账户余额
      status: null, // 建设银行不提供交易状态
      counterpartyAccount: counterpartyInfo.account, // 对方账号
      transactionId: null, // 建设银行不提供订单号
      merchantOrderId: null,
      memo: null,
      cashRemit: rawRow.cashRemit ? String(rawRow.cashRemit).trim() : null, // 钞汇类型
    });
  }

  return {
    drafts,
    warnings,
    source: "ccb",
    sourceType: "xls",
    rowCount: drafts.length,
  };
}
