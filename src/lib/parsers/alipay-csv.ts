import Papa from "papaparse";
import iconv from "iconv-lite";
import crypto from "crypto";
import type { UnifiedTransactionDraft, ParseWarning, ParseResult } from "../types";

/**
 * 支付宝 CSV 列名映射
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
 * 智能解码 Buffer（自动检测 UTF-8 / GBK）
 */
function smartDecode(buffer: ArrayBuffer): string {
  const uint8 = new Uint8Array(buffer);
  
  // 尝试 UTF-8
  try {
    const utf8 = new TextDecoder("utf-8", { fatal: true }).decode(uint8);
    // 检查是否包含中文关键词（确认解码成功）
    if (utf8.includes("交易时间") || utf8.includes("支付宝")) {
      return utf8;
    }
  } catch {
    // UTF-8 解码失败，继续尝试 GBK
  }
  
  // 使用 iconv-lite 解码 GBK/GB18030（更可靠）
  const nodeBuffer = Buffer.from(uint8);
  return iconv.decode(nodeBuffer, "gb18030");
}

/**
 * 查找标题行索引
 */
function findHeaderRowIndex(lines: string[]): number {
  for (let i = 0; i < Math.min(lines.length, 30); i++) {
    const line = lines[i];
    if (line.includes("交易时间") && (line.includes("金额") || line.includes("收/支"))) {
      return i;
    }
  }
  return -1;
}

/**
 * 标准化列名
 * 优先匹配更长的别名，避免 "对方账号" 被 "对方" 误匹配
 */
function normalizeColumnName(name: string): string {
  const trimmed = name.trim();
  
  // 收集所有匹配的候选项
  const matches: { standard: string; alias: string; length: number }[] = [];
  
  for (const [standard, aliases] of Object.entries(ALIPAY_COLUMN_ALIASES)) {
    for (const alias of aliases) {
      if (trimmed.includes(alias)) {
        matches.push({ standard, alias, length: alias.length });
      }
    }
  }
  
  // 按别名长度降序排序，选择最长的匹配
  if (matches.length > 0) {
    matches.sort((a, b) => b.length - a.length);
    return matches[0].standard;
  }
  
  return trimmed;
}

/**
 * 解析交易方向
 */
function parseDirection(value: string): "in" | "out" | null {
  const v = value.trim();
  if (v === "收入") return "in";
  if (v === "支出") return "out";
  if (v === "不计收支" || v === "") return null;
  return null;
}

/**
 * 解析金额
 */
function parseAmount(value: string): number {
  const cleaned = value.replace(/[,，\s]/g, "");
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : Math.abs(num);
}

/**
 * 解析对方账号（过滤掉 "/" 等无效值）
 */
function parseCounterpartyAccount(value: string | undefined): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  // "/" 表示无对方账号
  if (!trimmed || trimmed === "/" || trimmed === "-") return null;
  return trimmed;
}

/**
 * 解析日期时间
 */
function parseDateTime(value: string): Date | null {
  if (!value) return null;
  const trimmed = value.trim();
  const date = new Date(trimmed);
  return isNaN(date.getTime()) ? null : date;
}

/**
 * 支付宝 CSV 解析器
 */
export async function parseAlipayCsv(buffer: ArrayBuffer): Promise<ParseResult> {
  const content = smartDecode(buffer);
  const lines = content.split(/\r?\n/);
  
  // 查找标题行
  const headerIndex = findHeaderRowIndex(lines);
  if (headerIndex === -1) {
    throw new Error("无法找到标题行，请确认文件格式正确");
  }

  // 只解析数据部分
  const dataContent = lines.slice(headerIndex).join("\n");

  const parseResult = Papa.parse(dataContent, {
    header: true,
    skipEmptyLines: true,
    transformHeader: normalizeColumnName,
  });

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];
  let rowIndex = 0;

  for (const row of parseResult.data as Record<string, string>[]) {
    rowIndex++;

    // 跳过汇总行或空行
    if (!row.occurredAt || row.occurredAt.startsWith("-")) {
      continue;
    }

    // 解析时间
    const occurredAt = parseDateTime(row.occurredAt);
    if (!occurredAt) {
      warnings.push({
        row: headerIndex + rowIndex + 1,
        field: "occurredAt",
        message: `无效的交易时间: ${row.occurredAt}`,
      });
      continue;
    }

    // 解析方向
    const direction = parseDirection(row.direction || "");
    if (!direction) {
      // 跳过"不计收支"的记录，但不报警告
      continue;
    }

    // 解析金额
    const amount = parseAmount(row.amount || "0");
    if (amount === 0) {
      warnings.push({
        row: headerIndex + rowIndex + 1,
        field: "amount",
        message: `无效的金额: ${row.amount}`,
      });
      continue;
    }

    // 生成行 ID（优先使用交易订单号，否则使用行内容哈希避免跨文件冲突）
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
      accountName: row.paymentMethod?.trim() || null,
      source: "alipay",
      sourceRaw: JSON.stringify(row),
      sourceRowId,
      
      // ===== 扩展字段 =====
      balance: null, // 支付宝不提供余额
      status: row.status?.trim() || null, // 交易状态
      counterpartyAccount: parseCounterpartyAccount(row.counterpartyAccount), // 对方账号
      transactionId, // 交易订单号
      merchantOrderId: row.merchantOrderId?.trim() || null, // 商家订单号
      memo: row.memo?.trim() || null, // 备注
      cashRemit: null, // 支付宝不提供钞汇信息
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
