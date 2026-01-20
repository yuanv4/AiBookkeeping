/**
 * 账单来源
 */
export type BillSource = "alipay" | "ccb" | "cmb";

/**
 * 交易方向
 */
export type TransactionDirection = "in" | "out";

/**
 * 统一交易草稿结构
 * 包含所有数据源的完整字段
 */
export interface UnifiedTransactionDraft {
  // ===== 核心字段 =====
  occurredAt: Date;
  amount: number;
  direction: TransactionDirection;
  currency: string;
  counterparty: string | null;
  description: string | null;
  category: string | null;
  accountName: string | null;
  source: BillSource;
  sourceRaw: string; // 原始行 JSON
  sourceRowId: string;
  
  // ===== 扩展字段：覆盖所有数据源 =====
  
  // 余额相关（建设银行、招商银行）
  balance: number | null;
  
  // 交易状态（支付宝）
  status: string | null;
  
  // 对方账号信息
  counterpartyAccount: string | null;
  
  // 支付宝特有字段
  transactionId: string | null;
  merchantOrderId: string | null;
  memo: string | null;
  
  // 建设银行特有字段
  cashRemit: string | null;
}

/**
 * 解析警告
 */
export interface ParseWarning {
  row: number;
  field?: string;
  message: string;
}

/**
 * 解析结果
 */
export interface ParseResult {
  drafts: UnifiedTransactionDraft[];
  warnings: ParseWarning[];
  source: BillSource;
  sourceType: "csv" | "xls" | "pdf";
  rowCount: number;
}

/**
 * 导入批次创建参数
 */
export interface ImportBatchInput {
  fileName: string;
  fileSize: number;
  source: BillSource;
  sourceType: "csv" | "xls" | "pdf";
  rowCount: number;
  warningCount: number;
}

/**
 * 查询过滤条件
 */
export interface TransactionFilter {
  startDate?: Date;
  endDate?: Date;
  accountName?: string;
  direction?: TransactionDirection;
  keyword?: string;
  page?: number;
  pageSize?: number;
}

/**
 * 分页结果
 */
export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * API 响应
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
