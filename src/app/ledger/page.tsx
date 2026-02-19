"use client";

import { Fragment, useState, useEffect, useCallback } from "react";
import { Search, Filter, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AppShell } from "@/components/layout/app-shell";

interface TransactionRow {
  id: string;
  occurredAt: string;
  amount: number;
  direction: string;
  currency: string;
  counterparty: string | null;
  description: string | null;
  category: string | null;
  accountName: string | null;
  source: string;
  sourceRaw: string;
  sourceRowId: string;
  balance: number | null;
  status: string | null;
  counterpartyAccount: string | null;
  transactionId: string | null;
  merchantOrderId: string | null;
  memo: string | null;
  cashRemit: string | null;
  isDuplicate: boolean;
  duplicateGroupId: string | null;
  primaryTransactionId: string | null;
  duplicateReason: string | null;
  importBatchId: string;
  createdAt: string;
  updatedAt: string;
}

interface Stats {
  totalCount: number;
  totalExpense: number;
  totalIncome: number;
  netIncome: number;
}

type ColumnKey =
  | "occurredAt"
  | "direction"
  | "amount"
  | "counterparty"
  | "description"
  | "category"
  | "accountName"
  | "source"
  | "status";

const SOURCE_COLORS: Record<string, string> = {
  alipay: "bg-blue-500/20 text-blue-400",
  ccb: "bg-red-500/20 text-red-400",
  cmb: "bg-orange-500/20 text-orange-400",
  spdb: "bg-emerald-500/20 text-emerald-400",
};

const SOURCE_NAMES: Record<string, string> = {
  alipay: "支付宝",
  ccb: "建设银行",
  cmb: "招商银行",
  spdb: "浦发银行",
};

const MAIN_COLUMNS: Array<{ key: ColumnKey; label: string }> = [
  { key: "occurredAt", label: "交易时间" },
  { key: "direction", label: "方向" },
  { key: "amount", label: "金额" },
  { key: "counterparty", label: "对方" },
  { key: "description", label: "摘要" },
  { key: "category", label: "分类" },
  { key: "accountName", label: "账户" },
  { key: "source", label: "来源" },
  { key: "status", label: "状态" },
];

const DETAIL_FIELDS: Array<{ key: keyof TransactionRow; label: string }> = [
  { key: "currency", label: "币种" },
  { key: "balance", label: "余额" },
  { key: "counterpartyAccount", label: "对方账号" },
  { key: "transactionId", label: "交易订单号" },
  { key: "merchantOrderId", label: "商家订单号" },
  { key: "memo", label: "备注" },
  { key: "cashRemit", label: "钞汇类型" },
  { key: "sourceRowId", label: "来源行标识" },
  { key: "createdAt", label: "创建时间" },
  { key: "updatedAt", label: "更新时间" },
];

const DEBUG_FIELDS: Array<{ key: keyof TransactionRow; label: string }> = [
  { key: "id", label: "ID" },
  { key: "sourceRaw", label: "原始数据" },
  { key: "isDuplicate", label: "是否重复" },
  { key: "duplicateGroupId", label: "重复分组" },
  { key: "primaryTransactionId", label: "主记录ID" },
  { key: "duplicateReason", label: "重复原因" },
  { key: "importBatchId", label: "导入批次ID" },
];

export default function LedgerPage(): JSX.Element {
  const [transactions, setTransactions] = useState<TransactionRow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [keyword, setKeyword] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accounts, setAccounts] = useState<string[]>([]);
  const [direction, setDirection] = useState<"in" | "out" | "">("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);
  const [showDebugFields, setShowDebugFields] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const pageSize = 20;

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch("/api/ledger/stats");
      const result = await response.json();
      if (result.success) {
        setStats(result.data);
      }
    } catch (error) {
      console.error("获取统计数据失败:", error);
    }
  }, []);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        pageSize: String(pageSize),
      });

      if (keyword) params.set("keyword", keyword);
      if (accountName) params.set("accountName", accountName);
      if (direction) params.set("direction", direction);

      const response = await fetch(`/api/ledger/query?${params}`);
      const result = await response.json();

      if (result.success) {
        setTransactions(result.data.data);
        setTotalPages(result.data.totalPages);
        setTotal(result.data.total);
      }
    } catch (error) {
      console.error("获取交易记录失败:", error);
    } finally {
      setIsLoading(false);
    }
  }, [page, keyword, accountName, direction]);

  const fetchAccounts = useCallback(async () => {
    try {
      const response = await fetch("/api/ledger/accounts");
      const result = await response.json();
      if (result.success) {
        setAccounts(result.data);
      }
    } catch (error) {
      console.error("获取帐号列表失败:", error);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    fetchTransactions();
    setExpandedRowId(null);
  }, [fetchTransactions]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTransactions();
  };

  const handleClearAll = async () => {
    if (!window.confirm("确认清空所有账单与导入记录？此操作不可恢复。")) {
      return;
    }
    setIsClearing(true);
    try {
      const response = await fetch("/api/maintenance/clear", { method: "POST" });
      const result = await response.json();
      if (result.success) {
        setPage(1);
        setKeyword("");
        setAccountName("");
        setDirection("");
        await Promise.all([fetchStats(), fetchTransactions(), fetchAccounts()]);
      } else {
        console.error("清空失败:", result.error);
      }
    } catch (error) {
      console.error("清空失败:", error);
    } finally {
      setIsClearing(false);
    }
  };

  function handleExport(): void {
    const params = new URLSearchParams();
    if (keyword) params.set("keyword", keyword);
    if (accountName) params.set("accountName", accountName);
    if (direction) params.set("direction", direction);
    const query = params.toString();
    const url = query ? `/api/ledger/export?${query}` : "/api/ledger/export";
    window.location.assign(url);
  }

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });
  };

  const formatDirection = (dir: string): string => {
    return dir === "out" ? "支出" : "收入";
  };

  const formatAmount = (amount: number, dir: string): string => {
    const sign = dir === "out" ? "-" : "+";
    return `${sign}¥${amount.toFixed(2)}`;
  };

  const getSourceBadge = (src: string) => {
    return (
      <span className={`px-2 py-0.5 rounded text-xs ${SOURCE_COLORS[src] || "bg-muted"}`}>
        {SOURCE_NAMES[src] || src}
      </span>
    );
  };

  const formatValue = (row: TransactionRow, key: keyof TransactionRow): string | React.ReactNode => {
    const value = row[key];

    if (key === "source") {
      return getSourceBadge(String(value));
    }

    if (key === "occurredAt" || key === "createdAt" || key === "updatedAt") {
      return formatDate(String(value));
    }

    if (key === "direction") {
      return formatDirection(String(value));
    }

    if (key === "amount") {
      return (
        <span className={row.direction === "out" ? "text-destructive font-medium" : "text-primary font-medium"}>
          {formatAmount(Number(value), row.direction)}
        </span>
      );
    }

    if (key === "balance") {
      if (value === null) return "-";
      return `¥${Number(value).toFixed(2)}`;
    }

    if (typeof value === "boolean") {
      return value ? "是" : "否";
    }

    if (value === null || value === "") {
      return "-";
    }

    return String(value);
  };

  const detailFields = showDebugFields ? [...DETAIL_FIELDS, ...DEBUG_FIELDS] : DETAIL_FIELDS;

  return (
    <main className="min-h-screen bg-background">
      <AppShell title="统一账单" subtitle="收支对账与汇总" contentClassName="max-w-7xl mx-auto px-6 pb-16 pt-6 space-y-6">
        <Card className="animate-slide-up">
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="grid gap-4 lg:grid-cols-[1.6fr_1fr_0.8fr_auto]">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="搜索交易记录..."
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="pl-9"
                />
              </div>
              <select
                value={accountName}
                onChange={(e) => {
                  setAccountName(e.target.value);
                  setPage(1);
                }}
                className="h-10 px-3 rounded-xl border border-input bg-card/70 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">全部帐号</option>
                {accounts.map((account) => (
                  <option key={account} value={account}>
                    {account}
                  </option>
                ))}
              </select>
              <select
                value={direction}
                onChange={(e) => {
                  setDirection(e.target.value as "in" | "out" | "");
                  setPage(1);
                }}
                className="h-10 px-3 rounded-xl border border-input bg-card/70 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">全部类型</option>
                <option value="out">支出</option>
                <option value="in">收入</option>
              </select>
              <div className="flex flex-wrap items-center justify-start gap-2">
                <Button type="submit">
                  <Filter className="w-4 h-4 mr-2" />
                  筛选
                </Button>
                <Button type="button" variant="destructive" onClick={handleClearAll} disabled={isClearing}>
                  {isClearing ? "清空中..." : "清空数据"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-stagger">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">总交易笔数</p>
              <p className="text-2xl font-bold mt-2">{stats?.totalCount ?? 0}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">总支出</p>
              <p className="text-2xl font-bold text-destructive mt-2">¥{(stats?.totalExpense ?? 0).toFixed(2)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">总收入</p>
              <p className="text-2xl font-bold text-primary mt-2">¥{(stats?.totalIncome ?? 0).toFixed(2)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground ink-label">净收入</p>
              <p className={`text-2xl font-bold mt-2 ${(stats?.netIncome ?? 0) >= 0 ? "text-primary" : "text-destructive"}`}>
                ¥{(stats?.netIncome ?? 0).toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="animate-slide-up">
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <CardTitle>交易记录</CardTitle>
                <CardDescription>主表仅显示高频字段，点击“详情”查看完整信息</CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={showDebugFields}
                    onChange={(e) => setShowDebugFields(e.target.checked)}
                  />
                  显示调试字段
                </label>
                <p className="text-sm text-muted-foreground whitespace-nowrap">共 {total} 条记录</p>
                <Button type="button" variant="outline" size="sm" onClick={handleExport}>
                  导出 CSV
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : transactions.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">暂无交易记录，请先导入账单</div>
            ) : (
              <>
                <div className="overflow-x-auto rounded-lg border border-border/70">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/40">
                      <tr className="border-b border-border/70">
                        {MAIN_COLUMNS.map((column) => (
                          <th key={column.key} className="text-left py-3 px-4 font-medium whitespace-nowrap">
                            {column.label}
                          </th>
                        ))}
                        <th className="text-left py-3 px-4 font-medium whitespace-nowrap">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((row) => {
                        const isExpanded = expandedRowId === row.id;
                        return (
                          <Fragment key={row.id}>
                            <tr className="border-b border-border/50 hover:bg-muted/40">
                              {MAIN_COLUMNS.map((column) => (
                                <td
                                  key={`${row.id}-${column.key}`}
                                  className={`py-3 px-4 text-muted-foreground ${column.key === "description" ? "max-w-[240px] truncate" : "whitespace-nowrap"}`}
                                >
                                  {formatValue(row, column.key)}
                                </td>
                              ))}
                              <td className="py-3 px-4 whitespace-nowrap">
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setExpandedRowId(isExpanded ? null : row.id)}
                                >
                                  {isExpanded ? "收起" : "详情"}
                                </Button>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr className="border-b border-border/50 bg-muted/20">
                                <td colSpan={MAIN_COLUMNS.length + 1} className="p-4">
                                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {detailFields.map((field) => (
                                      <div key={`${row.id}-${field.key}`} className="rounded-md border border-border/60 bg-card/60 px-3 py-2">
                                        <p className="text-xs text-muted-foreground">{field.label}</p>
                                        <div className="text-sm break-all">{formatValue(row, field.key)}</div>
                                      </div>
                                    ))}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-6">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-sm text-muted-foreground px-4">第 {page} / {totalPages} 页</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </AppShell>
    </main>
  );
}
