/**
 * 账单导入 API 集成测试
 *
 * 测试完整的账单导入流程：
 * 1. 解析文件 (POST /api/import/parse)
 * 2. 提交数据 (POST /api/import/commit)
 *
 * 运行测试：
 * npm test -- import-bill.test.ts
 *
 * 前置条件：
 * 1. 启动本地服务（默认 http://localhost:3000，可用 BASE_URL 覆盖）
 * 2. 准备 src/__tests__/fixtures 目录下的测试账单文件
 */

import fs from "fs";
import path from "path";
import { beforeAll, describe, expect, test } from "vitest";

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_BASE_URL = "http://localhost:3000";

type ParseResponseData = { drafts: unknown[]; warnings: string[] };
type ParseResponse = {
  success: boolean;
  data?: ParseResponseData;
  error?: string;
};
type CommitResponse = {
  success: boolean;
  data?: { batchId: string; rowCount: number; skippedCount: number };
  error?: string;
};

function normalizeBaseUrl(rawBaseUrl?: string): string {
  if (!rawBaseUrl || rawBaseUrl === "/") {
    return DEFAULT_BASE_URL;
  }

  if (rawBaseUrl.startsWith("//")) {
    return `http:${rawBaseUrl}`;
  }

  if (!/^https?:\/\//i.test(rawBaseUrl)) {
    return `http://${rawBaseUrl.replace(/^\/+/, "")}`;
  }

  return rawBaseUrl.replace(/\/+$/, "");
}

const BASE_URL = normalizeBaseUrl(process.env.BASE_URL);

function buildTestFiles(repoRoot: string): string[] {
  const fixturesDir = path.join(repoRoot, "src", "__tests__", "fixtures");
  return [
    path.join(fixturesDir, "支付宝交易明细(20250101-20251231).csv"),
    path.join(fixturesDir, "建设银行交易流水(20250101-20251231).xls"),
    path.join(fixturesDir, "招商银行交易流水(20250101-20251231).pdf"),
  ];
}

function ensureFilesExist(files: string[]): void {
  const missing = files.filter((filePath) => !fs.existsSync(filePath));
  if (missing.length > 0) {
    throw new Error(`找不到测试文件: ${missing.join(", ")}`);
  }
}

function fileToBlob(filePath: string): Blob {
  const buffer = fs.readFileSync(filePath);
  return new Blob([buffer]);
}

async function requestParseFile(filePath: string): Promise<Response> {
  const formData = new FormData();

  const blob = fileToBlob(filePath);
  const fileName = path.basename(filePath);

  // 根据文件扩展名确定 source 和 sourceType
  const ext = path.extname(fileName).toLowerCase();
  let source: "alipay" | "ccb" | "cmb" | undefined;
  let sourceType: "csv" | "xls" | "pdf" | undefined;

  if (fileName.includes("支付宝")) {
    source = "alipay";
    sourceType = ext === ".csv" ? "csv" : undefined;
  } else if (fileName.includes("建设银行")) {
    source = "ccb";
    sourceType = ext === ".xls" || ext === ".xlsx" ? "xls" : undefined;
  } else if (fileName.includes("招商银行")) {
    source = "cmb";
    sourceType = ext === ".pdf" ? "pdf" : undefined;
  }

  formData.append("file", blob, fileName);
  if (source) formData.append("source", source);
  if (sourceType) formData.append("sourceType", sourceType);

  const response = await fetch(`${BASE_URL}/api/import/parse`, {
    method: "POST",
    body: formData,
  });

  return response;
}

async function requestCommitData(
  fileName: string,
  fileSize: number,
  source: "alipay" | "ccb" | "cmb",
  sourceType: "csv" | "xls" | "pdf",
  drafts: unknown[],
  warningCount: number
): Promise<Response> {
  const response = await fetch(`${BASE_URL}/api/import/commit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fileName,
      fileSize,
      source,
      sourceType,
      drafts,
      warningCount,
    }),
  });

  return response;
}

async function parseResponseJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

async function parseParseResponse(filePath: string): Promise<ParseResponse> {
  const response = await requestParseFile(filePath);
  expect(response.status).toBe(200);
  return parseResponseJson<ParseResponse>(response);
}

async function parseCommitResponse(
  fileName: string,
  fileSize: number,
  source: "alipay" | "ccb" | "cmb",
  sourceType: "csv" | "xls" | "pdf",
  drafts: unknown[],
  warningCount: number
): Promise<CommitResponse> {
  const response = await requestCommitData(
    fileName,
    fileSize,
    source,
    sourceType,
    drafts,
    warningCount
  );
  expect(response.status).toBe(200);
  return parseResponseJson<CommitResponse>(response);
}

function expectParseData(
  result: ParseResponse,
  requireRows: boolean
): ParseResponseData {
  expect(result.success).toBe(true);
  expect(result.data?.drafts).toBeDefined();
  expect(Array.isArray(result.data?.drafts)).toBe(true);
  if (requireRows) {
    expect(result.data?.drafts.length).toBeGreaterThan(0);
  }
  return result.data!;
}

const files = buildTestFiles(REPO_ROOT);
describe("账单导入 API 集成测试", () => {
  beforeAll(() => {
    ensureFilesExist(files);
  });

  test.concurrent("支付宝 CSV 文件解析", async () => {
    const result = await parseParseResponse(files[0]);
    expectParseData(result, true);
  });

  test.concurrent("建设银行 XLS 文件解析", async () => {
    const result = await parseParseResponse(files[1]);
    expectParseData(result, true);
  });

  test.concurrent("招商银行 PDF 文件解析", async () => {
    const result = await parseParseResponse(files[2]);
    expectParseData(result, true);
  });

  test("完整导入流程 - 解析并提交", { timeout: 120_000 }, async () => {
    // 1. 解析文件
    const parseResult = await parseParseResponse(files[0]);
    const { drafts, warnings } = expectParseData(parseResult, false);
    const stats = fs.statSync(files[0]);

    // 2. 提交数据
    const commitResult = await parseCommitResponse(
      path.basename(files[0]),
      stats.size,
      "alipay",
      "csv",
      drafts,
      warnings.length
    );

    expect(commitResult.success).toBe(true);
    expect(commitResult.data).toBeDefined();
    if (commitResult.data!.rowCount === 0) {
      expect(commitResult.data!.skippedCount).toBeGreaterThan(0);
      expect(commitResult.data!.batchId).toBe("");
    } else {
      expect(commitResult.data!.batchId).toBeTruthy();
      expect(commitResult.data!.rowCount).toBeGreaterThan(0);
    }
  });
});
