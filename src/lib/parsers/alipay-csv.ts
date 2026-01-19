import Papa from "papaparse";
import iconv from "iconv-lite";
import crypto from "crypto";
import type { UnifiedTransactionDraft, ParseWarning, ParseResult } from "../types";

/**
 * 支付宝 CSV 列名映射
 * 按别名长度降序排列，用于优先匹配更长的列名
 */
const ALIPAY_COLUMN_ALIASES: Record<string, string[]> = {
  occurredAt: ["交易时间", "交易创建时间"],
  category: ["交易分类", "交易类型"],
  counterparty: ["交易对方", "对方"],
  counterpartyAccount: ["对方账号"],
  description: ["商品说明", "商品名称", "备注"],
  direction: ["收/支", "收入/支出"],
  amount: ["金额", "金额（元）"],
  paymentMethod: ["收/付款方式", "支付方式"],
  status: ["交易状态", "状态"],
  transactionId: ["交易订单号", "交易号"],
  merchantOrderId: ["商家订单号"],
  memo: ["备注"],
};

/**
 * 反向映射：别名 -> 标准列名
 * 按别名长度降序排列，确保 "对方账号" 优先于 "对方" 匹配
 */
const ALIAS_TO_COLUMN: Array<{ alias: string; standard: string }> = (() => {
  const mapping: Array<{ alias: string; standard: string }> = [];

  for (const [standard, aliases] of Object.entries(ALIPAY_COLUMN_ALIASES)) {
    for (const alias of aliases) {
      mapping.push({ alias, standard });
    }
  }

  return mapping.sort((a, b) => b.alias.length - a.alias.length);
})();

/**
 * 智能解码 Buffer（自动检测 UTF-8 / GBK）
 */
function smartDecode(buffer: ArrayBuffer): string {
  const uint8 = new Uint8Array(buffer);

  try {
    const utf8 = new TextDecoder("utf-8", { fatal: true }).decode(uint8);
    if (utf8.includes("交易时间") || utf8.includes("支付宝")) {
      return utf8;
    }
  } catch {
    // UTF-8 解码失败，尝试 GBK
  }

  return iconv.decode(Buffer.from(uint8), "gb18030");
}

/**
 * 查找标题行索引
 */
function findHeaderRowIndex(lines: string[]): number {
  const maxRows = Math.min(lines.length, 30);

  for (let i = 0; i < maxRows; i++) {
    const line = lines[i];
    if (line.includes("交易时间") && (line.includes("金额") || line.includes("收/支"))) {
      return i;
    }
  }

  return -1;
}

/**
 * 标准化列名：将原始列名映射到标准字段名
 * 使用预排序的反向映射，优先匹配更长的别名
 */
function normalizeColumnName(name: string): string {
  const trimmed = name.trim();

  for (const { alias, standard } of ALIAS_TO_COLUMN) {
    if (trimmed.includes(alias)) {
      return standard;
    }
  }

  return trimmed;
}

/**
 * 解析交易方向
 */
function parseDirection(value: string): "in" | "out" | null {
  const trimmed = value.trim();
  if (trimmed === "收入") return "in";
  if (trimmed === "支出") return "out";
  return null;
}

/**
 * 解析金额（去除千分位分隔符）
 */
function parseAmount(value: string): number {
  const cleaned = value.replace(/[,，\s]/g, "");
  const num = parseFloat(cleaned);
  return Number.isNaN(num) ? 0 : Math.abs(num);
}

/**
 * 解析对方账号（过滤掉 "/" 等无效值）
 */
function parseCounterpartyAccount(value: string | undefined): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed || trimmed === "/" || trimmed === "-") return null;
  return trimmed;
}

/**
 * 解析日期时间
 */
function parseDateTime(value: string): Date | null {
  if (!value) return null;
  const date = new Date(value.trim());
  return Number.isNaN(date.getTime()) ? null : date;
}

/**
 * 从支付方式中提取账户名称，去除优惠活动信息
 * 例如： "招商银行储蓄卡(8516)&红包" -> "招商银行储蓄卡(8516)"
 */
function extractAccountName(paymentMethod: string): string | null {
  if (!paymentMethod) return null;
  const accountName = paymentMethod.split("&")[0].trim();
  return accountName || null;
}

/**
 * 支付宝 CSV 解析器
 */
export async function parseAlipayCsv(buffer: ArrayBuffer): Promise<ParseResult> {
  const content = smartDecode(buffer);
  const lines = content.split(/\r?\n/);

  const headerIndex = findHeaderRowIndex(lines);
  if (headerIndex === -1) {
    throw new Error("无法找到标题行，请确认文件格式正确");
  }

  const parseResult = Papa.parse(lines.slice(headerIndex).join("\n"), {
    header: true,
    skipEmptyLines: true,
    transformHeader: normalizeColumnName,
  });

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];
  let rowIndex = 0;

  for (const row of parseResult.data as Record<string, string>[]) {
    rowIndex++;

    if (!row.occurredAt || row.occurredAt.startsWith("-")) {
      continue;
    }

    const occurredAt = parseDateTime(row.occurredAt);
    if (!occurredAt) {
      warnings.push({
        row: headerIndex + rowIndex + 1,
        field: "occurredAt",
        message: `无效的交易时间: ${row.occurredAt}`,
      });
      continue;
    }

    const direction = parseDirection(row.direction || "");
    if (!direction) {
      continue;
    }

    const amount = parseAmount(row.amount || "0");
    if (amount === 0) {
      warnings.push({
        row: headerIndex + rowIndex + 1,
        field: "amount",
        message: `无效的金额: ${row.amount}`,
      });
      continue;
    }

    const transactionId = row.transactionId?.trim() || null;
    const rawKey = JSON.stringify(row);
    const hash = crypto.createHash("sha1").update(rawKey).digest("hex");
    const sourceRowId = transactionId || `hash-${hash}`;

    drafts.push({
      occurredAt,
      amount,
      direction,
      currency: "CNY",
      counterparty: row.counterparty?.trim() || null,
      description: row.description?.trim() || null,
      category: row.category?.trim() || null,
      accountName: extractAccountName(row.paymentMethod?.trim() || ""),
      source: "alipay",
      sourceRaw: JSON.stringify(row),
      sourceRowId,

      // 扩展字段
      balance: null,
      status: row.status?.trim() || null,
      counterpartyAccount: parseCounterpartyAccount(row.counterpartyAccount),
      transactionId,
      merchantOrderId: row.merchantOrderId?.trim() || null,
      memo: row.memo?.trim() || null,
      cashRemit: null,
    });
  }

  return {
    drafts,
    warnings,
    source: "alipay",
    sourceType: "csv",
    rowCount: drafts.length,
  };
}
