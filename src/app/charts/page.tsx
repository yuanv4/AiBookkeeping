"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Sparkles, Copy, RefreshCw, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

export default function ChartsPage() {
  const [prompt, setPrompt] = useState("");
  const [source, setSource] = useState<BillSource | "">("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [chartOption, setChartOption] = useState<EChartsOption | null>(null);
  const [optionJson, setOptionJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

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
    color: ["#22c55e", "#3b82f6", "#f59e0b", "#a855f7", "#ef4444"],
    backgroundColor: "transparent",
    textStyle: {
      color: "#a1a1aa",
    },
    title: {
      textStyle: {
        color: "#fafafa",
      },
      subtextStyle: {
        color: "#a1a1aa",
      },
    },
    legend: {
      textStyle: {
        color: "#a1a1aa",
      },
    },
    tooltip: {
      backgroundColor: "rgba(30, 41, 59, 0.9)",
      borderColor: "#334155",
      textStyle: {
        color: "#fafafa",
      },
    },
    xAxis: {
      axisLine: {
        lineStyle: {
          color: "#334155",
        },
      },
      axisLabel: {
        color: "#a1a1aa",
      },
      splitLine: {
        lineStyle: {
          color: "#1e293b",
        },
      },
    },
    yAxis: {
      axisLine: {
        lineStyle: {
          color: "#334155",
        },
      },
      axisLabel: {
        color: "#a1a1aa",
      },
      splitLine: {
        lineStyle: {
          color: "#1e293b",
        },
      },
    },
  };

  return (
    <main className="min-h-screen bg-background">
      {/* 导航栏 */}
      <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/" className="text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-semibold text-lg">AI 图表分析</h1>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* 提示词输入 */}
        <Card>
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
                className="h-10 px-3 rounded-md border border-input bg-background text-sm"
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
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 图表预览 */}
          <Card>
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
          <Card>
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
                <pre className="bg-muted/30 rounded-lg p-4 overflow-auto h-[400px] text-sm font-mono">
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
      </div>
    </main>
  );
}
