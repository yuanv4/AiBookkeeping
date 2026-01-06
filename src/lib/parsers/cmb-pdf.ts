import type { UnifiedTransactionDraft, ParseWarning, ParseResult } from "../types";

// 动态导入 pdf-parse（仅服务端使用）
let PDFParse: typeof import("pdf-parse").PDFParse;

async function getPDFParse() {
  if (!PDFParse) {
    const mod = await import("pdf-parse");
    PDFParse = mod.PDFParse;
  }
  return PDFParse;
}

/**
 * 解析日期 (YYYY-MM-DD 格式)
 */
function parseDate(value: string): Date | null {
  if (!value) return null;
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const [, year, month, day] = match;
  return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
}

/**
 * 解析金额
 */
function parseAmount(value: string): { amount: number; direction: "in" | "out" } | null {
  if (!value) return null;
  const cleaned = value.replace(/[,，\s]/g, "");
  const num = parseFloat(cleaned);
  if (isNaN(num) || num === 0) return null;
  return {
    amount: Math.abs(num),
    direction: num > 0 ? "in" : "out",
  };
}

/**
 * 解析余额
 */
function parseBalance(value: string): number | null {
  if (!value) return null;
  const cleaned = value.replace(/[,，\s]/g, "");
  const num = parseFloat(cleaned);
  return isNaN(num) ? null : num;
}

/**
 * 检查是否为日期行
 */
function isDateLine(line: string): boolean {
  return /^\d{4}-\d{2}-\d{2}/.test(line.trim());
}

/**
 * 解析交易行
 */
function parseLine(line: string): {
  date: string;
  currency: string;
  amount: string;
  balance: string;
  summary: string;
  counterparty: string;
} | null {
  const trimmed = line.trim();
  if (!isDateLine(trimmed)) return null;

  // 匹配模式: 日期 货币 金额 余额 摘要 对方
  // 例如: 2025-01-01 CNY -5.00 2,271.86 快捷支付 扫二维码付款
  const dateMatch = trimmed.match(/^(\d{4}-\d{2}-\d{2})/);
  if (!dateMatch) return null;

  const date = dateMatch[1];
  const rest = trimmed.slice(date.length).trim();

  // 解析货币
  const currencyMatch = rest.match(/^(CNY|USD|EUR|GBP|JPY|HKD)/i);
  if (!currencyMatch) return null;

  const currency = currencyMatch[1].toUpperCase();
  let remaining = rest.slice(currency.length).trim();

  // 解析金额 (可能为负数)
  const amountMatch = remaining.match(/^(-?[\d,]+\.?\d*)/);
  if (!amountMatch) return null;

  const amount = amountMatch[1];
  remaining = remaining.slice(amount.length).trim();

  // 解析余额
  const balanceMatch = remaining.match(/^(-?[\d,]+\.?\d*)/);
  if (!balanceMatch) return null;

  const balance = balanceMatch[1];
  remaining = remaining.slice(balance.length).trim();

  // 剩余部分为摘要和对方信息
  // 尝试分割：常见摘要关键词
  const summaryKeywords = [
    "快捷支付", "快捷退款", "银联快捷支付", "代发工资", "朝朝宝转出",
    "集中代收", "提回定借", "业务付款", "转账", "ATM取款",
    "利息", "手续费", "跨行转账", "网银转账"
  ];

  let summary = "";
  let counterparty = remaining;

  for (const keyword of summaryKeywords) {
    const idx = remaining.indexOf(keyword);
    if (idx !== -1) {
      // 找到关键词后，判断摘要的结束位置
      const afterKeyword = remaining.slice(idx);
      // 摘要可能包含多个词，用空格分隔
      const parts = afterKeyword.split(/\s+/);
      
      // 寻找摘要结束点：通常对方信息不以这些关键词开头
      let summaryEnd = parts[0].length;
      if (parts.length > 1 && parts[1].includes("业务付款")) {
        summaryEnd += 1 + parts[1].length;
      }
      
      summary = afterKeyword.slice(0, summaryEnd).trim();
      counterparty = afterKeyword.slice(summaryEnd).trim();
      break;
    }
  }

  if (!summary) {
    // 如果没有找到关键词，尝试简单分割
    const parts = remaining.split(/\s+/);
    if (parts.length >= 2) {
      summary = parts[0];
      counterparty = parts.slice(1).join(" ");
    } else {
      summary = remaining;
      counterparty = "";
    }
  }

  return {
    date,
    currency,
    amount,
    balance,
    summary,
    counterparty,
  };
}

/**
 * 招商银行 PDF 解析器
 */
export async function parseCmbPdf(buffer: ArrayBuffer): Promise<ParseResult> {
  const PDFParseClass = await getPDFParse();
  const parser = new PDFParseClass({ data: new Uint8Array(buffer) });
  
  const result = await parser.getText();
  const text = result.text;

  // 分割成行
  const lines = text.split("\n");

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];
  let rowIndex = 0;

  // 跳过头部信息，找到数据行
  let currentLine = "";
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 跳过空行和标题行
    if (!line) continue;
    if (line.startsWith("记账日期")) continue;
    if (line.startsWith("Date")) continue;
    if (line.includes("招商银行交易流水")) continue;
    if (line.includes("Transaction Statement")) continue;
    if (line.match(/^\d+\/\d+$/)) continue; // 页码
    if (line.startsWith("-- ")) continue; // 分页标记
    if (line.includes("户 名") || line.includes("账号")) continue;
    if (line.includes("Name") || line.includes("Account")) continue;
    if (line.includes("验 证 码")) continue;
    if (line.includes("Currency")) continue;

    // 累积行（处理跨行的情况）
    if (isDateLine(line)) {
      // 处理之前累积的行
      if (currentLine) {
        const parsed = parseLine(currentLine);
        if (parsed) {
          processTransaction(parsed, rowIndex, drafts, warnings);
        }
        rowIndex++;
      }
      currentLine = line;
    } else if (currentLine) {
      // 继续累积当前交易的信息
      currentLine += " " + line;
    }
  }

  // 处理最后一行
  if (currentLine) {
    const parsed = parseLine(currentLine);
    if (parsed) {
      processTransaction(parsed, rowIndex, drafts, warnings);
    }
  }

  return {
    drafts,
    warnings,
    source: "cmb",
    sourceType: "pdf",
    rowCount: drafts.length,
  };
}

/**
 * 清理并截断字符串
 */
function cleanAndTruncate(value: string | null | undefined, maxLength: number): string | null {
  if (!value) return null;
  // 清理多余的分隔线、水印等杂质
  let cleaned = value
    .replace(/[—─━]+/g, "") // 移除分隔线
    .replace(/温馨提示[：:].*$/s, "") // 移除温馨提示及之后内容
    .replace(/交易流水验真.*$/s, "") // 移除验真提示
    .replace(/www\.cmbchina\.com.*$/s, "") // 移除网址
    .replace(/\s+/g, " ") // 合并空白
    .trim();
  
  if (cleaned.length > maxLength) {
    cleaned = cleaned.substring(0, maxLength);
  }
  return cleaned || null;
}

/**
 * 处理交易记录
 */
function processTransaction(
  parsed: NonNullable<ReturnType<typeof parseLine>>,
  rowIndex: number,
  drafts: UnifiedTransactionDraft[],
  warnings: ParseWarning[]
) {
  const occurredAt = parseDate(parsed.date);
  if (!occurredAt) {
    warnings.push({
      row: rowIndex + 1,
      field: "date",
      message: `无效的交易日期: ${parsed.date}`,
    });
    return;
  }

  const amountInfo = parseAmount(parsed.amount);
  if (!amountInfo) {
    // 跳过金额为0的记录
    return;
  }

  // 解析余额
  const balance = parseBalance(parsed.balance);

  // 生成行 ID
  const sourceRowId = `cmb-${rowIndex}-${occurredAt.getTime()}-${amountInfo.amount}`;

  // 清理并截断字段以符合数据库约束
  const counterparty = cleanAndTruncate(parsed.counterparty, 200);
  const description = cleanAndTruncate(parsed.summary, 500);

  drafts.push({
    occurredAt,
    amount: amountInfo.amount,
    direction: amountInfo.direction,
    currency: parsed.currency === "CNY" ? "CNY" : parsed.currency,
    counterparty,
    description,
    category: null, // PDF 中没有分类信息
    accountName: "招商银行",
    source: "cmb",
    sourceRaw: JSON.stringify(parsed),
    sourceRowId,
    
    // ===== 扩展字段 =====
    balance, // 联机余额
    status: null, // 招商银行不提供交易状态
    counterpartyAccount: null, // 招商银行 PDF 不提供对方账号
    transactionId: null, // 招商银行不提供订单号
    merchantOrderId: null,
    memo: null,
    cashRemit: null, // 招商银行不提供钞汇信息
  });
}
