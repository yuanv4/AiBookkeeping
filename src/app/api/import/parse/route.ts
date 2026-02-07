import { NextRequest, NextResponse } from "next/server";
import { parseFile } from "@/lib/parsers";
import type { ApiResponse, ParseResult, BillSource } from "@/lib/types";

// 文件大小限制 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;
// 行数限制 5000
const MAX_ROWS = 5000;
const ALLOWED_TYPES = [
  "text/csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/pdf",
];
const ALLOWED_EXTENSIONS = [".csv", ".xls", ".xlsx", ".pdf"];

function isAllowedFile(file: File): boolean {
  const fileName = file.name.toLowerCase();
  return ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTENSIONS.some((ext) => fileName.endsWith(ext));
}

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<ParseResult>>> {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const sourceType = formData.get("sourceType") as "csv" | "xls" | "pdf" | null;
    const source = formData.get("source") as BillSource | null;

    if (!file) {
      return NextResponse.json(
        { success: false, error: "请上传文件" },
        { status: 400 }
      );
    }

    // 检查文件大小
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: `文件大小超过限制（最大 ${MAX_FILE_SIZE / 1024 / 1024}MB）` },
        { status: 400 }
      );
    }

    // 检查文件类型
    // 有些浏览器可能会使用不同的 MIME 类型
    if (!isAllowedFile(file)) {
      return NextResponse.json(
        { success: false, error: "不支持的文件类型，请上传 CSV、XLS 或 PDF 文件" },
        { status: 400 }
      );
    }

    // 读取文件内容
    const buffer = await file.arrayBuffer();

    // 解析文件
    const result = await parseFile(
      buffer,
      file.name,
      sourceType || undefined,
      source || undefined
    );

    // 检查行数限制
    if (result.drafts.length > MAX_ROWS) {
      return NextResponse.json(
        { success: false, error: `解析行数超过限制（最大 ${MAX_ROWS} 行）` },
        { status: 400 }
      );
    }

    return NextResponse.json({
      success: true,
      data: result,
    });
  } catch (error) {
    console.error("解析文件失败:", error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "解析文件失败" },
      { status: 500 }
    );
  }
}
