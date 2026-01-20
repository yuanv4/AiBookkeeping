import type { UnifiedTransactionDraft, ParseWarning, ParseResult } from "../types";

/**
 * 从PDF文本中提取账号
 */
function extractAccountNumber(text: string): string | null {
  const match = text.match(/账号[：:]\s*(\d{4}\*{8}\d{4})/);
  return match?.[1] || null;
}

/**
 * 生成标准化的账户名称
 * 格式：招商银行储蓄卡(尾号)
 */
function generateAccountName(accountNumber: string | null): string {
  if (!accountNumber) return "招商银行";
  const tailNumber = accountNumber.slice(-4);
  return `招商银行储蓄卡(${tailNumber})`;
}

/**
 * 动态导入 pdf-parse（仅服务端使用）
 */
let PDFParse: typeof import("pdf-parse").PDFParse;

async function getPDFParse(): Promise<typeof import("pdf-parse").PDFParse> {
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
  return new Date(
    Date.UTC(
      Number.parseInt(year, 10),
      Number.parseInt(month, 10) - 1,
      Number.parseInt(day, 10)
    )
  );
}

/**
 * 解析金额
 */
function parseNumber(value: string): number | null {
  if (!value) return null;
  const cleaned = value.replace(/[,，\s]/g, "");
  const num = Number.parseFloat(cleaned);
  return Number.isNaN(num) ? null : num;
}

function parseAmount(value: string): { amount: number; direction: "in" | "out" } | null {
  const num = parseNumber(value);
  if (!num) return null;
  return {
    amount: Math.abs(num),
    direction: num > 0 ? "in" : "out",
  };
}

/**
 * 解析余额
 */
function parseBalance(value: string): number | null {
  return parseNumber(value);
}

/**
 * 检查是否为日期行
 */
function isDateLine(line: string): boolean {
  return /^\d{4}-\d{2}-\d{2}/.test(line.trim());
}

/**
 * 摘要关键词列表
 */
const SUMMARY_KEYWORDS = [
  "快捷支付",
  "快捷退款",
  "银联快捷支付",
  "代发工资",
  "朝朝宝转出",
  "集中代收",
  "提回定借",
  "业务付款",
  "转账",
  "ATM取款",
  "利息",
  "手续费",
  "跨行转账",
  "网银转账",
] as const;

/**
 * 解析交易行
 */
interface ParsedTransactionLine {
  date: string;
  currency: string;
  amount: string;
  balance: string;
  summary: string;
  counterparty: string;
}

function parseLine(line: string): ParsedTransactionLine | null {
  const trimmed = line.trim();
  if (!isDateLine(trimmed)) return null;

  const dateMatch = trimmed.match(/^(\d{4}-\d{2}-\d{2})/);
  if (!dateMatch) return null;

  const date = dateMatch[1];
  let remaining = trimmed.slice(date.length).trim();

  const currencyMatch = remaining.match(/^(CNY|USD|EUR|GBP|JPY|HKD)/i);
  if (!currencyMatch) return null;

  const currency = currencyMatch[1].toUpperCase();
  remaining = remaining.slice(currencyMatch[1].length).trim();

  const amountMatch = remaining.match(/^(-?[\d,]+\.?\d*)/);
  if (!amountMatch) return null;

  const amount = amountMatch[1];
  remaining = remaining.slice(amountMatch[1].length).trim();

  const balanceMatch = remaining.match(/^(-?[\d,]+\.?\d*)/);
  if (!balanceMatch) return null;

  const balance = balanceMatch[1];
  remaining = remaining.slice(balanceMatch[1].length).trim();

  const { summary, counterparty } = parseSummaryAndCounterparty(remaining);

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
 * 解析摘要和对方信息
 * @internal
 */
export function parseSummaryAndCounterparty(
  remaining: string
): { summary: string; counterparty: string } {
  for (const keyword of SUMMARY_KEYWORDS) {
    const idx = remaining.indexOf(keyword);
    if (idx === -1) continue;

    const afterKeyword = remaining.slice(idx);
    const parts = afterKeyword.split(/\s+/);

    let summaryEnd = parts[0].length;
    if (parts.length > 1 && parts[1].includes("业务付款")) {
      summaryEnd += 1 + parts[1].length;
    }

    return {
      summary: afterKeyword.slice(0, summaryEnd).trim(),
      counterparty: afterKeyword.slice(summaryEnd).trim(),
    };
  }

  const parts = remaining.split(/\s+/);
  if (parts.length >= 2) {
    return {
      summary: parts[0],
      counterparty: parts.slice(1).join(" "),
    };
  }

  return {
    summary: remaining,
    counterparty: "",
  };
}

/**
 * 检查是否为需要跳过的行
 */
function isSkipLine(line: string): boolean {
  if (!line) return true;
  const skipPatterns = [
    "记账日期",
    "Date",
    "招商银行交易流水",
    "Transaction Statement",
    "-- ",
    "户 名",
    "账号",
    "Name",
    "Account",
    "验 证 码",
    "Currency",
  ];
  if (skipPatterns.some((pattern) => line.includes(pattern))) return true;
  if (/^\d+\/\d+$/.test(line)) return true;
  return false;
}

/**
 * 招商银行 PDF 解析器
 */
export async function parseCmbPdf(buffer: ArrayBuffer): Promise<ParseResult> {
  const PDFParseClass = await getPDFParse();
  const parser = new PDFParseClass({ data: new Uint8Array(buffer) });

  const { text } = await parser.getText();

  const accountNumber = extractAccountNumber(text);
  const accountName = generateAccountName(accountNumber);

  const lines = text.split("\n");

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];
  let rowIndex = 0;
  let currentLine = "";

  for (const line of lines) {
    const trimmed = line.trim();

    if (isSkipLine(trimmed)) continue;

    if (isDateLine(trimmed)) {
      if (currentLine) {
        const parsed = parseLine(currentLine);
        if (parsed) {
          processTransaction(parsed, rowIndex, drafts, warnings, accountName);
        }
        rowIndex++;
      }
      currentLine = trimmed;
    } else if (currentLine) {
      currentLine += " " + trimmed;
    }
  }

  if (currentLine) {
    const parsed = parseLine(currentLine);
    if (parsed) {
      processTransaction(parsed, rowIndex, drafts, warnings, accountName);
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

  let cleaned = value
    .replace(/[—─━]+/g, "")
    .replace(/温馨提示[：:].*$/s, "")
    .replace(/交易流水验真.*$/s, "")
    .replace(/www\.cmbchina\.com.*$/s, "")
    .replace(/\s+/g, " ")
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
  parsed: ParsedTransactionLine,
  rowIndex: number,
  drafts: UnifiedTransactionDraft[],
  warnings: ParseWarning[],
  accountName: string
): void {
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
  if (!amountInfo) return;

  const balance = parseBalance(parsed.balance);
  const sourceRowId = `cmb-${rowIndex}-${occurredAt.getTime()}-${amountInfo.amount}`;

  drafts.push({
    occurredAt,
    amount: amountInfo.amount,
    direction: amountInfo.direction,
    currency: parsed.currency,
    counterparty: cleanAndTruncate(parsed.counterparty, 200),
    description: cleanAndTruncate(parsed.summary, 500),
    category: null,
    accountName,
    source: "cmb",
    sourceRaw: JSON.stringify(parsed),
    sourceRowId,
    balance,
    status: null,
    counterpartyAccount: null,
    transactionId: null,
    merchantOrderId: null,
    memo: null,
    cashRemit: null,
  });
}
