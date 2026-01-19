import * as XLSX from "xlsx";
import type { UnifiedTransactionDraft, ParseWarning, ParseResult } from "../types";

/**
 * 建设银行 XLS 列名映射
 */
const CCB_COLUMN_ALIASES: Record<string, string[]> = {
  index: ["序号"],
  summary: ["摘要"],
  currency: ["币别"],
  cashRemit: ["钞汇"],
  date: ["交易日期"],
  amount: ["交易金额"],
  balance: ["账户余额"],
  location: ["交易地点/附言", "交易地点", "附言"],
  counterparty: ["对方账号与户名", "对方账号", "对方户名"],
  accountNumber: ["卡号/账号", "账号", "卡号"],
};

/**
 * 标题行查找结果
 */
interface HeaderRowResult {
  rowIndex: number;
  columnMap: Record<string, number>;
  accountNumber: string | null;
}

/**
 * 从行中提取卡号
 */
function extractAccountNumberFromRow(rowStr: string[]): string | null {
  for (const cell of rowStr) {
    const match = cell.match(/卡号\/账号[：:]\s*(\d{16,19})/);
    if (match) return match[1];
  }
  return null;
}

/**
 * 检查行是否包含关键列名
 */
function hasKeyColumns(rowStr: string[]): boolean {
  return (
    rowStr.some((c) => c.includes("交易日期")) &&
    rowStr.some((c) => c.includes("交易金额"))
  );
}

/**
 * 构建列映射
 */
function buildColumnMap(rowStr: string[]): Record<string, number> {
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

  return columnMap;
}

/**
 * 查找标题行和卡号
 */
function findHeaderRow(data: unknown[][]): HeaderRowResult | null {
  let accountNumber: string | null = null;
  const maxRows = Math.min(data.length, 10);

  for (let i = 0; i < maxRows; i++) {
    const row = data[i];
    if (!Array.isArray(row)) continue;

    const rowStr = row.map((c) => String(c || "").trim());

    if (!accountNumber) {
      accountNumber = extractAccountNumberFromRow(rowStr);
    }

    if (hasKeyColumns(rowStr)) {
      const columnMap = buildColumnMap(rowStr);
      return { rowIndex: i, columnMap, accountNumber };
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

  if (/^\d{8}$/.test(str)) {
    const year = Number.parseInt(str.substring(0, 4), 10);
    const month = Number.parseInt(str.substring(4, 6), 10) - 1;
    const day = Number.parseInt(str.substring(6, 8), 10);
    return new Date(year, month, day);
  }

  const date = new Date(str);
  return Number.isNaN(date.getTime()) ? null : date;
}

/**
 * 解析金额和方向
 */
function parseAmount(value: unknown): { amount: number; direction: "in" | "out" } | null {
  const num = toNumber(value);
  if (num === null || num === 0) return null;

  return {
    amount: Math.abs(num),
    direction: num > 0 ? "in" : "out",
  };
}

/**
 * 解析对方信息（格式：账号/户名）
 */
function parseCounterparty(value: unknown): { account: string | null; name: string | null } {
  if (!value) return { account: null, name: null };

  const str = String(value).trim();

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
 * 将值转换为数字
 */
function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;

  const num =
    typeof value === "number"
      ? value
      : parseFloat(String(value).replace(/[,，\s]/g, ""));

  return Number.isNaN(num) ? null : num;
}

/**
 * 解析余额
 */
function parseBalance(value: unknown): number | null {
  return toNumber(value);
}

/**
 * 生成标准化的账户名称
 * 格式：建设银行储蓄卡(尾号) 或 建设银行(尾号)
 */
function generateAccountName(accountNumber: string | null): string {
  if (!accountNumber) return "建设银行";

  const tailNumber = accountNumber.slice(-4);
  const firstDigit = accountNumber.charAt(0);
  const cardType = firstDigit === "4" || firstDigit === "5" ? "信用卡" : "储蓄卡";

  return `建设银行${cardType}(${tailNumber})`;
}

/**
 * 建设银行 XLS 解析器
 */
export async function parseCcbXls(buffer: ArrayBuffer): Promise<ParseResult> {
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  const data = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    blankrows: false,
  }) as unknown[][];

  const headerInfo = findHeaderRow(data);
  if (!headerInfo) {
    throw new Error("无法找到标题行，请确认文件格式正确");
  }

  const { rowIndex: headerRowIndex, columnMap, accountNumber } = headerInfo;
  const accountName = generateAccountName(accountNumber);

  if (columnMap.date === undefined || columnMap.amount === undefined) {
    throw new Error("缺少必要列：交易日期或交易金额");
  }

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];

  for (let i = headerRowIndex + 1; i < data.length; i++) {
    const row = data[i];
    if (!Array.isArray(row) || row.length === 0) continue;

    const rowNum = i + 1;
    const rawRow: Record<string, unknown> = {};

    for (const [key, colIndex] of Object.entries(columnMap)) {
      rawRow[key] = row[colIndex];
    }

    const occurredAt = parseDate(rawRow.date);
    if (!occurredAt) {
      warnings.push({
        row: rowNum,
        field: "date",
        message: `无效的交易日期: ${rawRow.date}`,
      });
      continue;
    }

    const amountInfo = parseAmount(rawRow.amount);
    if (!amountInfo) continue;

    const counterpartyInfo = parseCounterparty(rawRow.counterparty);
    const balance = parseBalance(rawRow.balance);
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
      accountName,
      source: "ccb",
      sourceRaw: JSON.stringify(rawRow),
      sourceRowId,

      // 扩展字段
      balance,
      status: null,
      counterpartyAccount: counterpartyInfo.account,
      transactionId: null,
      merchantOrderId: null,
      memo: null,
      cashRemit: rawRow.cashRemit ? String(rawRow.cashRemit).trim() : null,
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
