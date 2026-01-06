import type { ParseResult, BillSource } from "../types";
import { parseAlipayCsv } from "./alipay-csv";
import { parseCcbXls } from "./ccb-xls";
import { parseCmbPdf } from "./cmb-pdf";

/**
 * 根据文件类型和来源自动选择解析器
 */
export async function parseFile(
  buffer: ArrayBuffer,
  fileName: string,
  sourceType?: "csv" | "xls" | "pdf",
  source?: BillSource
): Promise<ParseResult> {
  // 根据文件名推断类型
  const lowerName = fileName.toLowerCase();
  
  let detectedType = sourceType;
  let detectedSource = source;
  
  // 推断文件类型
  if (!detectedType) {
    if (lowerName.endsWith(".csv")) {
      detectedType = "csv";
    } else if (lowerName.endsWith(".xls") || lowerName.endsWith(".xlsx")) {
      detectedType = "xls";
    } else if (lowerName.endsWith(".pdf")) {
      detectedType = "pdf";
    }
  }
  
  // 推断来源
  if (!detectedSource) {
    if (lowerName.includes("支付宝") || lowerName.includes("alipay")) {
      detectedSource = "alipay";
    } else if (lowerName.includes("建设银行") || lowerName.includes("ccb")) {
      detectedSource = "ccb";
    } else if (lowerName.includes("招商银行") || lowerName.includes("cmb")) {
      detectedSource = "cmb";
    }
  }
  
  // 根据类型和来源选择解析器
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
