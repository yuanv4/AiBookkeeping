import type { ParseResult, ParseWarning, UnifiedTransactionDraft } from "../types";

let PDFParse: typeof import("pdf-parse").PDFParse;

async function getPDFParse(): Promise<typeof import("pdf-parse").PDFParse> {
  if (!PDFParse) {
    const mod = await import("pdf-parse");
    PDFParse = mod.PDFParse;
  }
  return PDFParse;
}

function extractAccountNumber(text: string): string | null {
  const match = text.match(/账号[:：]\s*(\d{10,})/);
  return match?.[1] ?? null;
}

function generateAccountName(accountNumber: string | null): string {
  if (!accountNumber) return "浦发银行";
  return `浦发银行储蓄卡(${accountNumber.slice(-4)})`;
}

function parseDateTime(dateText: string, timeText: string): Date | null {
  const match = `${dateText}${timeText}`.match(
    /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$/
  );
  if (!match) return null;

  const [, year, month, day, hour, minute, second] = match;
  return new Date(
    Date.UTC(
      Number.parseInt(year, 10),
      Number.parseInt(month, 10) - 1,
      Number.parseInt(day, 10),
      Number.parseInt(hour, 10),
      Number.parseInt(minute, 10),
      Number.parseInt(second, 10)
    )
  );
}

function parseNumber(value: string): number | null {
  const cleaned = value.replace(/[,，\s]/g, "");
  const parsed = Number.parseFloat(cleaned);
  return Number.isNaN(parsed) ? null : parsed;
}

function parseAmount(value: string): { amount: number; direction: "in" | "out" } | null {
  const num = parseNumber(value);
  if (num == null || num === 0) return null;
  return {
    amount: Math.abs(num),
    direction: num > 0 ? "in" : "out",
  };
}

function cleanText(lines: string[]): string | null {
  const value = lines.join("").replace(/\s+/g, " ").trim();
  return value || null;
}

function isHeaderLine(line: string): boolean {
  if (!line) return true;
  if (/^\d+\/\d+$/.test(line)) return true;
  if (/^第\d+页\/共\d+页/.test(line)) return true;
  if (/^--\s*\d+\s*of\s*\d+\s*--$/i.test(line)) return true;

  const headerKeywords = [
    "上海浦东发展银行个人客户交易流水专用回单",
    "Transaction Statement of Shanghai Pudong Development Bank",
    "户名:",
    "Name:",
    "币种:",
    "Currency:",
    "交易日期",
    "Date",
    "交易时间",
    "Time",
    "交易账号",
    "Transaction",
    "Account",
    "交易名称",
    "Name",
    "交易金额",
    "Amount",
    "账户余额",
    "Balance",
    "对手姓名",
    "Counter",
    "Party",
    "对手账号",
    "Opponent",
    "交易摘要",
    "Summary",
  ];

  return headerKeywords.some((k) => line === k || line.includes(k));
}

function isRecordStart(line: string): boolean {
  return /^\d{8}\s+\d{6}\s+\d{6,}$/.test(line);
}

interface ParsedRecord {
  occurredAt: Date;
  amount: number;
  direction: "in" | "out";
  balance: number | null;
  description: string | null;
  counterparty: string | null;
  counterpartyAccount: string | null;
  summary: string | null;
}

function parseRecord(lines: string[]): ParsedRecord | null {
  if (lines.length === 0) return null;

  const headMatch = lines[0].match(/^(\d{8})\s+(\d{6})\s+(\d{6,})$/);
  if (!headMatch) return null;

  const occurredAt = parseDateTime(headMatch[1], headMatch[2]);
  if (!occurredAt) return null;

  const body = lines.slice(1);
  if (body.length === 0) return null;

  if (/^\d{1,10}$/.test(body[0])) {
    body.shift();
  }

  let amountIndex = -1;
  for (let i = 0; i < body.length; i += 1) {
    if (/^-?[\d,]+(?:\.\d+)?\s+-?[\d,]+(?:\.\d+)?(?:\s+.*)?$/.test(body[i])) {
      amountIndex = i;
      break;
    }
  }
  if (amountIndex === -1) return null;

  const description = cleanText(body.slice(0, amountIndex));
  const amountLine = body[amountIndex];
  const amountMatch = amountLine.match(
    /^(-?[\d,]+(?:\.\d+)?)\s+(-?[\d,]+(?:\.\d+)?)(?:\s+(.*))?$/
  );
  if (!amountMatch) return null;

  const amountInfo = parseAmount(amountMatch[1]);
  if (!amountInfo) return null;

  const balance = parseNumber(amountMatch[2]);
  const remainder = amountMatch[3] ? [amountMatch[3], ...body.slice(amountIndex + 1)] : body.slice(amountIndex + 1);

  let counterpartyAccount: string | null = null;
  let summary: string | null = null;
  let counterpartyLines = remainder;

  const firstNumericIndex = remainder.findIndex((line) => /^[\d*]+$/.test(line));
  if (firstNumericIndex >= 0) {
    const accountParts: string[] = [];
    let index = firstNumericIndex;
    while (index < remainder.length && /^[\d*]+$/.test(remainder[index])) {
      accountParts.push(remainder[index]);
      index += 1;
    }
    counterpartyLines = remainder.slice(0, firstNumericIndex);
    counterpartyAccount = accountParts.join("");
    summary = cleanText(remainder.slice(index));
  }

  return {
    occurredAt,
    amount: amountInfo.amount,
    direction: amountInfo.direction,
    balance,
    description,
    counterparty: cleanText(counterpartyLines),
    counterpartyAccount,
    summary,
  };
}

export async function parseSpdbPdf(buffer: ArrayBuffer): Promise<ParseResult> {
  const PDFParseClass = await getPDFParse();
  const parser = new PDFParseClass({ data: new Uint8Array(buffer) });
  const { text } = await parser.getText();

  const accountNumber = extractAccountNumber(text);
  const accountName = generateAccountName(accountNumber);
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !isHeaderLine(line));

  const recordBlocks: string[][] = [];
  let current: string[] = [];

  for (const line of lines) {
    if (isRecordStart(line)) {
      if (current.length > 0) {
        recordBlocks.push(current);
      }
      current = [line];
      continue;
    }
    if (current.length > 0) {
      current.push(line);
    }
  }
  if (current.length > 0) {
    recordBlocks.push(current);
  }

  const drafts: UnifiedTransactionDraft[] = [];
  const warnings: ParseWarning[] = [];

  recordBlocks.forEach((block, index) => {
    const parsed = parseRecord(block);
    if (!parsed) {
      warnings.push({
        row: index + 1,
        message: "无法识别的浦发流水记录",
      });
      return;
    }

    const sourceRowId = `spdb-${index}-${parsed.occurredAt.getTime()}-${parsed.amount}`;
    drafts.push({
      occurredAt: parsed.occurredAt,
      amount: parsed.amount,
      direction: parsed.direction,
      currency: "CNY",
      counterparty: parsed.counterparty,
      description: parsed.summary ?? parsed.description,
      category: null,
      accountName,
      source: "spdb",
      sourceRaw: JSON.stringify(parsed),
      sourceRowId,
      balance: parsed.balance,
      status: null,
      counterpartyAccount: parsed.counterpartyAccount,
      transactionId: null,
      merchantOrderId: null,
      memo: null,
      cashRemit: null,
    });
  });

  return {
    drafts,
    warnings,
    source: "spdb",
    sourceType: "pdf",
    rowCount: drafts.length,
  };
}
