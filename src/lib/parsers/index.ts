import type { ParseResult, BillSource } from "../types";
import { parseAlipayCsv } from "./alipay-csv";
import { parseCcbXls } from "./ccb-xls";
import { parseCmbPdf } from "./cmb-pdf";

function inferSource(lowerName: string): BillSource | undefined {
  if (lowerName.includes("支付宝") || lowerName.includes("alipay")) {
    return "alipay";
  }
  if (lowerName.includes("建设银行") || lowerName.includes("ccb")) {
    return "ccb";
  }
  if (lowerName.includes("招商银行") || lowerName.includes("cmb")) {
    return "cmb";
  }
  return undefined;
}

function inferType(lowerName: string): "csv" | "xls" | "pdf" | undefined {
  if (lowerName.endsWith(".csv")) return "csv";
  if (lowerName.endsWith(".xls") || lowerName.endsWith(".xlsx")) return "xls";
  if (lowerName.endsWith(".pdf")) return "pdf";
  return undefined;
}

/**
 * 根据文件类型和来源自动选择解析器
 */
export async function parseFile(
  buffer: ArrayBuffer,
  fileName: string,
  sourceType?: "csv" | "xls" | "pdf",
  source?: BillSource
): Promise<ParseResult> {
  const lowerName = fileName.toLowerCase();

  const detectedType = sourceType ?? inferType(lowerName);
  const detectedSource = source ?? inferSource(lowerName);

  if (detectedType === "csv") {
    if (!detectedSource || detectedSource === "alipay") {
      return parseAlipayCsv(buffer);
    }
    throw new Error(`不支持的 CSV 来源: ${detectedSource}`);
  }

  if (detectedType === "xls") {
    if (!detectedSource || detectedSource === "ccb") {
      return parseCcbXls(buffer);
    }
    throw new Error(`不支持的 XLS 来源: ${detectedSource}`);
  }

  if (detectedType === "pdf") {
    if (!detectedSource || detectedSource === "cmb") {
      return parseCmbPdf(buffer);
    }
    throw new Error(`不支持的 PDF 来源: ${detectedSource}`);
  }

  throw new Error(`无法识别文件类型，请确认文件格式正确: ${fileName}`);
}

export { parseAlipayCsv } from "./alipay-csv";
export { parseCcbXls } from "./ccb-xls";
export { parseCmbPdf } from "./cmb-pdf";
