"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles, Copy, RefreshCw, Check, Loader2, Clock, Database, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AppShell } from "@/components/layout/app-shell";
import type { BillSource, EChartsOption } from "@/lib/types";

// 动态导入 ECharts
import dynamic from "next/dynamic";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface SavedChart {
  id: string;
  title: string;
  option: EChartsOption;
  createdAt: string;
  kind: "system" | "user";
}

export default function ChartsPage() {
  const [prompt, setPrompt] = useState("");
  const [source, setSource] = useState<BillSource | "">("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [chartOption, setChartOption] = useState<EChartsOption | null>(null);
  const [optionJson, setOptionJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [savedCharts, setSavedCharts] = useState<SavedChart[]>([]);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [savedError, setSavedError] = useState<string | null>(null);
  const [presetStartDate, setPresetStartDate] = useState("");
  const [presetEndDate, setPresetEndDate] = useState("");
  const [showOption, setShowOption] = useState(false);
  const [chartKey, setChartKey] = useState(0);
  const [showHistory, setShowHistory] = useState(false);
  const [lastGeneratedAt, setLastGeneratedAt] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const closeHistory = () => setShowHistory(false);
  const applyChartOption = (option: EChartsOption) => {
    setChartOption(option);
    setOptionJson(JSON.stringify(option, null, 2));
    setChartKey((prev) => prev + 1);
  };

  const fetchSavedCharts = async () => {
    setIsLoadingSaved(true);
    setSavedError(null);

    try {
      const response = await fetch("/api/charts/saved");
      const result = await response.json();
      if (!result.success) {
        setSavedError(result.error || "获取已保存图表失败");
        return;
      }
      setSavedCharts(result.data || []);
    } catch (err) {
      setSavedError(err instanceof Error ? err.message : "获取已保存图表失败");
    } finally {
      setIsLoadingSaved(false);
    }
  };

  useEffect(() => {
    fetchSavedCharts();
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError("请输入提示词");
      return;
    }

    setIsGenerating(true);
    setError(null);
    setChartOption(null);
    setOptionJson("");

    try {
      const response = await fetch("/api/charts/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          startDate: presetStartDate || undefined,
          endDate: presetEndDate || undefined,
          source: source || undefined,
        }),
      });

      const result = await response.json();

      if (!result.success) {
        setError(result.error || "生成失败");
        return;
      }

      applyChartOption(result.data.option);
      setLastGeneratedAt(new Date().toLocaleString("zh-CN"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplySaved = (item: SavedChart) => {
    applyChartOption(item.option);
    setPrompt(item.title);
    setError(null);
    setLastGeneratedAt(new Date(item.createdAt).toLocaleString("zh-CN"));
    closeHistory();
  };

  const handleSaveChart = async () => {
    if (!chartOption) {
      setError("请先生成图表");
      return;
    }

    setError(null);
    setSaveSuccess(null);

    try {
      const response = await fetch("/api/charts/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: prompt || "已保存图表",
          prompt,
          option: chartOption,
          dataFilter: {
            startDate: presetStartDate || undefined,
            endDate: presetEndDate || undefined,
            source: source || undefined,
          },
        }),
      });

      const result = await response.json();
      if (!result.success) {
        setError(result.error || "保存失败");
        return;
      }

      setSaveSuccess("已保存图表");
      fetchSavedCharts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    }
  };

  const handleSeedPresets = async () => {
    try {
      const response = await fetch("/api/charts/presets/seed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          startDate: presetStartDate || undefined,
          endDate: presetEndDate || undefined,
          source: source || undefined,
        }),
      });
      const result = await response.json();
      if (!result.success) {
        setSavedError(result.error || "初始化系统示例失败");
        return;
      }
      fetchSavedCharts();
    } catch (err) {
      setSavedError(err instanceof Error ? err.message : "初始化系统示例失败");
    }
  };

  const handleCopy = async () => {
    if (!optionJson) return;
    
    try {
      await navigator.clipboard.writeText(optionJson);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("复制失败");
    }
  };

  const handleRegenerate = () => {
    if (prompt) {
      handleGenerate();
    }
  };

  // 图表颜色主题
  const chartTheme = {
    color: ["#d24f28", "#2f9f8d", "#2f6fa3", "#f3b33d", "#e24949"],
    backgroundColor: "transparent",
    textStyle: {
      color: "#4b5563",
    },
    title: {
      textStyle: {
        color: "#1f2937",
      },
      subtextStyle: {
        color: "#6b7280",
      },
    },
    legend: {
      textStyle: {
        color: "#6b7280",
      },
    },
    tooltip: {
      backgroundColor: "rgba(252, 248, 241, 0.95)",
      borderColor: "#d4c7b6",
      textStyle: {
        color: "#1f2937",
      },
    },
    xAxis: {
      axisLine: {
        lineStyle: {
          color: "#d4c7b6",
        },
      },
      axisLabel: {
        color: "#6b7280",
      },
      splitLine: {
        lineStyle: {
          color: "rgba(212, 199, 182, 0.5)",
        },
      },
    },
    yAxis: {
      axisLine: {
        lineStyle: {
          color: "#d4c7b6",
        },
      },
      axisLabel: {
        color: "#6b7280",
      },
      splitLine: {
        lineStyle: {
          color: "rgba(212, 199, 182, 0.5)",
        },
      },
    },
  };

  return (
    <main className="min-h-screen bg-background">
      <AppShell title="AI 图表分析" subtitle="图表分析" contentClassName="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl font-semibold">图表分析控制台</h2>
            <p className="text-sm text-muted-foreground">围绕数据范围、提示词与生成结果进行分析与管理</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>{lastGeneratedAt ? `最近生成：${lastGeneratedAt}` : "尚未生成图表"}</span>
          </div>
        </div>

        <Card className="bg-card/80 border-border/70 shadow-sm">
          <CardHeader>
            <CardTitle>交互流程</CardTitle>
            <CardDescription>按步骤完成筛选、生成、预览与复用</CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            {(error || saveSuccess) && (
              <div className="space-y-3">
                {error && (
                  <div className="rounded-lg border border-destructive/50 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                )}
                {saveSuccess && (
                  <div className="rounded-lg border border-primary/40 bg-primary/5 px-4 py-3 text-sm text-primary">
                    {saveSuccess}
                  </div>
                )}
              </div>
            )}

            <section className="relative space-y-4 pl-10">
              <div className="absolute left-0 top-0 flex h-7 w-7 items-center justify-center rounded-full bg-chart-2/15 text-xs font-semibold text-chart-2">
                1
              </div>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-chart-2" />
                <p className="text-sm font-medium">选择数据范围</p>
              </div>
              <p className="text-xs text-muted-foreground">先限定时间与来源，避免生成结果过于泛化。</p>
              <div className="grid gap-3">
                <label className="text-sm text-muted-foreground">时间范围</label>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <input
                    type="date"
                    value={presetStartDate}
                    onChange={(e) => setPresetStartDate(e.target.value)}
                    className="h-10 rounded-md border border-input bg-card/80 px-3 text-sm"
                  />
                  <input
                    type="date"
                    value={presetEndDate}
                    onChange={(e) => setPresetEndDate(e.target.value)}
                    className="h-10 rounded-md border border-input bg-card/80 px-3 text-sm"
                  />
                </div>
              </div>
              <div className="grid gap-3">
                <label className="text-sm text-muted-foreground">账单来源</label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value as BillSource | "")}
                  className="h-10 px-3 rounded-md border border-input bg-card/80 text-sm"
                >
                  <option value="">全部来源</option>
                  <option value="alipay">支付宝</option>
                  <option value="ccb">建设银行</option>
                  <option value="cmb">招商银行</option>
                </select>
              </div>
            </section>

            <div className="h-px bg-border/60" />

            <section className="relative space-y-4 pl-10">
              <div className="absolute left-0 top-0 flex h-7 w-7 items-center justify-center rounded-full bg-accent/15 text-xs font-semibold text-accent">
                2
              </div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-accent" />
                <p className="text-sm font-medium">输入生成指令</p>
              </div>
              <Input
                type="text"
                placeholder="例如：按月份统计支出趋势、显示各类别支出占比饼图..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
              />
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={handleGenerate} disabled={isGenerating}>
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      生成图表
                    </>
                  )}
                </Button>
                <Button variant="outline" size="sm" onClick={handleSeedPresets}>
                  初始化系统示例
                </Button>
                <Button variant="outline" size="sm" onClick={fetchSavedCharts} disabled={isLoadingSaved}>
                  刷新历史
                </Button>
              </div>
            </section>

            <div className="h-px bg-border/60" />

            <section className="relative space-y-4 pl-10">
              <div className="absolute left-0 top-0 flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                3
              </div>
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-medium">查看图表结果</p>
                  <p className="text-xs text-muted-foreground">生成完成后可直接保存或继续迭代。</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowHistory(true)}
                  >
                    <History className="w-4 h-4 mr-2" />
                    历史
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSaveChart}
                    disabled={!chartOption}
                  >
                    保存
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRegenerate}
                    disabled={!prompt || isGenerating}
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${isGenerating ? "animate-spin" : ""}`} />
                    重新生成
                  </Button>
                </div>
              </div>
              <div ref={chartRef} className="w-full h-[420px] rounded-xl border border-border/60 bg-muted/20 flex items-center justify-center">
                {isGenerating ? (
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p>AI 正在生成图表...</p>
                  </div>
                ) : chartOption ? (
                  <ReactECharts
                    key={chartKey}
                    option={chartOption}
                    style={{ width: "100%", height: "100%" }}
                    theme={chartTheme}
                    opts={{ renderer: "canvas" }}
                  />
                ) : (
                  <div className="text-center text-muted-foreground space-y-2">
                    <p>输入提示词并生成图表</p>
                    <p className="text-xs">提示：选择数据范围后，生成更准确</p>
                  </div>
                )}
              </div>

              <div className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">配置详情</p>
                    <p className="text-xs text-muted-foreground">查看与复制 ECharts 配置 JSON</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowOption((prev) => !prev)}
                    >
                      {showOption ? "收起配置" : "查看配置"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopy}
                      disabled={!optionJson}
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4 mr-2" />
                          已复制
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-2" />
                          复制
                        </>
                      )}
                    </Button>
                  </div>
                </div>
                {showOption && (
                  <div className="relative mt-4">
                    <pre className="bg-muted/40 rounded-lg p-4 overflow-auto h-[320px] text-sm font-mono">
                      {optionJson || `// 生成的 ECharts option 将显示在这里
{
  "title": { ... },
  "xAxis": { ... },
  "yAxis": { ... },
  "series": [ ... ]
}`}
                    </pre>
                  </div>
                )}
              </div>

            </section>
          </CardContent>
        </Card>

        {showHistory && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 px-4"
            onClick={closeHistory}
          >
            <div
              className="w-full max-w-3xl rounded-2xl border border-border/70 bg-card shadow-xl"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-border/60 px-5 py-4">
                <div className="flex items-center gap-2">
                  <History className="w-5 h-5 text-primary" />
                  <p className="text-sm font-medium">历史图表</p>
                </div>
                <Button variant="outline" size="sm" onClick={closeHistory}>
                  关闭
                </Button>
              </div>
              <div className="max-h-[60vh] overflow-auto px-5 py-4">
                {isLoadingSaved ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>加载中...</span>
                  </div>
                ) : savedError ? (
                  <p className="text-sm text-destructive">{savedError}</p>
                ) : savedCharts.length === 0 ? (
                  <p className="text-sm text-muted-foreground">暂无已保存图表</p>
                ) : (
                  <div className="space-y-3">
                    {savedCharts.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handleApplySaved(item)}
                        className="w-full text-left p-3 rounded-xl border border-border/70 bg-card/80 hover:border-primary/50 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="font-medium">{item.title}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {new Date(item.createdAt).toLocaleString("zh-CN")}
                            </p>
                          </div>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              item.kind === "system"
                                ? "bg-primary/10 text-primary"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {item.kind === "system" ? "系统" : "个人"}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </AppShell>
    </main>
  );
}
