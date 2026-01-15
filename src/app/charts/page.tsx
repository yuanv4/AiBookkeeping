"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles, Copy, RefreshCw, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AppShell } from "@/components/layout/app-shell";
import type { BillSource, EChartsOption } from "@/lib/types";

// 动态导入 ECharts
import dynamic from "next/dynamic";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const PRESET_PROMPTS = [
  "按月份统计收支趋势",
  "支出类别占比饼图",
  "每日收支柱状图",
  "各来源账单金额对比",
];

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
  const [copied, setCopied] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

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
          source: source || undefined,
        }),
      });

      const result = await response.json();

      if (!result.success) {
        setError(result.error || "生成失败");
        return;
      }

      setChartOption(result.data.option);
      setOptionJson(JSON.stringify(result.data.option, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplySaved = (item: SavedChart) => {
    setChartOption(item.option);
    setOptionJson(JSON.stringify(item.option, null, 2));
    setPrompt(item.title);
    setError(null);
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

  const handlePresetClick = (preset: string) => {
    setPrompt(preset);
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
        {/* 已保存图表 */}
        <Card className="bg-card/80 border-border/70 shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <CardTitle>已保存图表</CardTitle>
            </div>
            <CardDescription>
              包含系统预置与个人保存的图表配置
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">开始日期</span>
                <input
                  type="date"
                  value={presetStartDate}
                  onChange={(e) => setPresetStartDate(e.target.value)}
                  className="h-9 rounded-md border border-input bg-card/80 px-3 text-sm"
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">结束日期</span>
                <input
                  type="date"
                  value={presetEndDate}
                  onChange={(e) => setPresetEndDate(e.target.value)}
                  className="h-9 rounded-md border border-input bg-card/80 px-3 text-sm"
                />
              </div>
              <Button variant="outline" size="sm" onClick={handleSeedPresets}>
                初始化系统示例
              </Button>
              <Button variant="outline" size="sm" onClick={fetchSavedCharts} disabled={isLoadingSaved}>
                刷新列表
              </Button>
            </div>
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
              <div className="grid gap-4 md:grid-cols-3">
                {savedCharts.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleApplySaved(item)}
                    className="text-left p-4 rounded-xl border border-border/70 bg-card/80 hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{item.title}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        item.kind === "system" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                      }`}>
                        {item.kind === "system" ? "系统" : "个人"}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      {new Date(item.createdAt).toLocaleString("zh-CN")}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 提示词输入 */}
        <Card className="bg-card/80 border-border/70 shadow-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent" />
              <CardTitle>智能图表生成</CardTitle>
            </div>
            <CardDescription>
              输入自然语言描述，AI 将自动生成对应的可视化图表
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <Input
                type="text"
                placeholder="例如：按月份统计支出趋势、显示各类别支出占比饼图..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                className="flex-1"
              />
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
            </div>

            {/* 预设提示词 */}
            <div className="flex flex-wrap gap-2">
              {PRESET_PROMPTS.map((preset) => (
                <Button
                  key={preset}
                  variant="outline"
                  size="sm"
                  onClick={() => handlePresetClick(preset)}
                  className="text-xs"
                >
                  {preset}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 错误提示 */}
        {error && (
          <Card className="border-destructive bg-card/80 shadow-sm">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {saveSuccess && (
          <Card className="border-primary bg-card/80 shadow-sm">
            <CardContent className="pt-6">
              <p className="text-primary">{saveSuccess}</p>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 图表预览 */}
          <Card className="bg-card/80 border-border/70 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>图表预览</CardTitle>
                  <CardDescription>生成的图表将在此显示</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div ref={chartRef} className="w-full h-[400px] flex items-center justify-center">
                {isGenerating ? (
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p>AI 正在生成图表...</p>
                  </div>
                ) : chartOption ? (
                  <ReactECharts
                    option={chartOption}
                    style={{ width: "100%", height: "100%" }}
                    theme={chartTheme}
                    opts={{ renderer: "canvas" }}
                  />
                ) : (
                  <p className="text-muted-foreground">输入提示词生成图表</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Option JSON */}
          <Card className="bg-card/80 border-border/70 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>ECharts Option</CardTitle>
                  <CardDescription>生成的图表配置 JSON</CardDescription>
                </div>
                <div className="flex gap-2">
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
            </CardHeader>
            <CardContent>
              <div className="relative">
                <pre className="bg-muted/40 rounded-lg p-4 overflow-auto h-[400px] text-sm font-mono">
                  {optionJson || `// 生成的 ECharts option 将显示在这里
{
  "title": { ... },
  "xAxis": { ... },
  "yAxis": { ... },
  "series": [ ... ]
}`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    </main>
  );
}
