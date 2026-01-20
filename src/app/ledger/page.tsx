"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Filter, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AppShell } from "@/components/layout/app-shell";

interface Transaction {
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
  importBatch: {
    fileName: string;
  };
}

interface Stats {
  totalCount: number;
  totalExpense: number;
  totalIncome: number;
  netIncome: number;
}

const SOURCE_COLORS: Record<string, string> = {
  alipay: "bg-blue-500/20 text-blue-400",
  ccb: "bg-red-500/20 text-red-400",
  cmb: "bg-orange-500/20 text-orange-400",
};

const SOURCE_NAMES: Record<string, string> = {
  alipay: "支付宝",
  ccb: "建行",
  cmb: "招行",
};

export default function LedgerPage(): JSX.Element {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [keyword, setKeyword] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accounts, setAccounts] = useState<string[]>([]);
  const [direction, setDirection] = useState<"in" | "out" | "">("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
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

  const formatAmount = (amount: number, direction: string): string => {
    const sign = direction === "out" ? "-" : "+";
    return `${sign}¥${amount.toFixed(2)}`;
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getSourceBadge = (source: string) => {
    return (
      <span className={`px-2 py-0.5 rounded text-xs ${SOURCE_COLORS[source] || "bg-muted"}`}>
        {SOURCE_NAMES[source] || source}
      </span>
    );
  };

  return (
    <main className="min-h-screen bg-background">
      <AppShell title="统一账单" subtitle="统一账单" contentClassName="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* 搜索和筛选 */}
        <Card className="bg-card/80 border-border/70 shadow-sm">
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="flex items-center gap-4">
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
                className="h-10 px-3 rounded-md border border-input bg-card/80 text-sm"
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
                className="h-10 px-3 rounded-md border border-input bg-card/80 text-sm"
              >
                <option value="">全部类型</option>
                <option value="out">支出</option>
                <option value="in">收入</option>
              </select>
              <Button type="submit">
                <Filter className="w-4 h-4 mr-2" />
                筛选
              </Button>
              <Button type="button" variant="destructive" onClick={handleClearAll} disabled={isClearing}>
                {isClearing ? "清空中..." : "清空数据"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-card/80 border-border/70 shadow-sm">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">总交易笔数</p>
              <p className="text-2xl font-bold mt-1">{stats?.totalCount ?? 0}</p>
            </CardContent>
          </Card>
          <Card className="bg-card/80 border-border/70 shadow-sm">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">总支出</p>
              <p className="text-2xl font-bold text-destructive mt-1">
                ¥{(stats?.totalExpense ?? 0).toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-card/80 border-border/70 shadow-sm">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">总收入</p>
              <p className="text-2xl font-bold text-primary mt-1">
                ¥{(stats?.totalIncome ?? 0).toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-card/80 border-border/70 shadow-sm">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">净收入</p>
              <p className={`text-2xl font-bold mt-1 ${
                (stats?.netIncome ?? 0) >= 0 ? "text-primary" : "text-destructive"
              }`}>
                ¥{(stats?.netIncome ?? 0).toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 交易列表 */}
        <Card className="bg-card/80 border-border/70 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>交易记录</CardTitle>
                <CardDescription>显示所有来源的统一账单数据</CardDescription>
              </div>
              <p className="text-sm text-muted-foreground">
                共 {total} 条记录
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : transactions.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                暂无交易记录，请先导入账单
              </div>
            ) : (
              <>
                <div className="overflow-x-auto rounded-lg border border-border/70">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/40">
                      <tr className="border-b border-border/70">
                        <th className="text-left py-3 px-4 font-medium">时间</th>
                        <th className="text-left py-3 px-4 font-medium">来源</th>
                        <th className="text-left py-3 px-4 font-medium">帐号</th>
                        <th className="text-left py-3 px-4 font-medium">对方</th>
                        <th className="text-left py-3 px-4 font-medium">描述</th>
                        <th className="text-right py-3 px-4 font-medium">金额</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((t) => (
                        <tr key={t.id} className="border-b border-border/50 hover:bg-muted/40">
                          <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">
                            {formatDate(t.occurredAt)}
                          </td>
                          <td className="py-3 px-4">{getSourceBadge(t.source)}</td>
                          <td className="py-3 px-4 max-w-[180px] truncate">
                            {t.accountName || "-"}
                          </td>
                          <td className="py-3 px-4 max-w-[150px] truncate">
                            {t.counterparty || "-"}
                          </td>
                          <td className="py-3 px-4 text-muted-foreground max-w-[200px] truncate">
                            {t.description || t.category || "-"}
                          </td>
                          <td className={`py-3 px-4 text-right font-medium whitespace-nowrap ${
                            t.direction === "out" ? "text-destructive" : "text-primary"
                          }`}>
                            {formatAmount(t.amount, t.direction)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 分页 */}
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
                    <span className="text-sm text-muted-foreground px-4">
                      第 {page} / {totalPages} 页
                    </span>
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
