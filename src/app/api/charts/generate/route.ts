import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import prisma from "@/lib/db";
import { ChartGenerateRequestSchema, EChartsOptionSchema } from "@/lib/types";
import type { ApiResponse, EChartsOption } from "@/lib/types";

interface ChartGenerateResult {
  option: EChartsOption;
  requestId: string;
}

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse<ChartGenerateResult>>> {
  try {
    const body = await request.json();
    const { prompt, startDate, endDate, source } = ChartGenerateRequestSchema.parse(body);

    // 构建查询条件
    const where: Record<string, unknown> = {};
    
    if (startDate || endDate) {
      where.occurredAt = {};
      if (startDate) {
        (where.occurredAt as Record<string, Date>).gte = new Date(startDate);
      }
      if (endDate) {
        (where.occurredAt as Record<string, Date>).lte = new Date(endDate);
      }
    }
    
    if (source) {
      where.source = source;
    }

    // 获取交易数据
    const transactions = await prisma.transaction.findMany({
      where,
      orderBy: { occurredAt: "asc" },
      take: 1000, // 限制数据量
      select: {
        occurredAt: true,
        amount: true,
        direction: true,
        category: true,
        counterparty: true,
        source: true,
      },
    });

    if (transactions.length === 0) {
      return NextResponse.json(
        { success: false, error: "没有找到符合条件的交易数据" },
        { status: 400 }
      );
    }

    // 准备数据摘要
    const dataSummary = prepareDataSummary(transactions);

    // 调用 Anthropic API
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey || apiKey === "your-anthropic-api-key-here") {
      return NextResponse.json(
        { success: false, error: "请配置 ANTHROPIC_API_KEY 环境变量" },
        { status: 500 }
      );
    }

    const client = new Anthropic({ apiKey });

    const systemPrompt = `你是一个数据可视化专家，擅长根据用户需求生成 ECharts 图表配置。

你将收到一段交易数据摘要，以及用户的可视化需求。请根据这些信息生成一个有效的 ECharts option JSON。

要求：
1. 只输出纯 JSON，不要包含任何 markdown 或其他格式
2. 确保 JSON 格式正确，可以直接被 JSON.parse 解析
3. 使用中文作为图表标题和标签
4. 颜色方案使用：["#22c55e", "#3b82f6", "#f59e0b", "#a855f7", "#ef4444"]
5. series 数量不超过 10 个
6. 数据点数量不超过 100 个
7. 不要在 formatter 中使用函数，只使用字符串模板`;

    const userPrompt = `数据摘要：
${dataSummary}

用户需求：${prompt}

请生成 ECharts option JSON：`;

    const response = await client.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 4096,
      messages: [
        { role: "user", content: userPrompt },
      ],
      system: systemPrompt,
    });

    // 提取 JSON
    const content = response.content[0];
    if (content.type !== "text") {
      throw new Error("AI 返回格式错误");
    }

    let optionJson: unknown;
    try {
      // 尝试直接解析
      optionJson = JSON.parse(content.text);
    } catch {
      // 尝试从 markdown 代码块中提取
      const jsonMatch = content.text.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (jsonMatch) {
        optionJson = JSON.parse(jsonMatch[1].trim());
      } else {
        throw new Error("无法解析 AI 返回的 JSON");
      }
    }

    // 校验 option
    const validatedOption = EChartsOptionSchema.parse(optionJson);

    // 保存请求记录
    const chartRequest = await prisma.chartRequest.create({
      data: {
        prompt,
        dataFilter: JSON.stringify({ startDate, endDate, source }),
        optionJson: JSON.stringify(validatedOption),
      },
    });

    return NextResponse.json({
      success: true,
      data: {
        option: validatedOption,
        requestId: chartRequest.id,
      },
    });
  } catch (error) {
    console.error("生成图表失败:", error);
    
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : "生成图表失败" },
      { status: 500 }
    );
  }
}

/**
 * 准备数据摘要
 */
function prepareDataSummary(transactions: Array<{
  occurredAt: Date;
  amount: number;
  direction: string;
  category: string | null;
  counterparty: string | null;
  source: string;
}>): string {
  // 按月统计
  const monthlyStats = new Map<string, { income: number; expense: number }>();
  
  // 按分类统计
  const categoryStats = new Map<string, number>();
  
  // 按来源统计
  const sourceStats = new Map<string, number>();

  for (const t of transactions) {
    // 月份
    const month = t.occurredAt.toISOString().slice(0, 7);
    const monthData = monthlyStats.get(month) || { income: 0, expense: 0 };
    if (t.direction === "in") {
      monthData.income += t.amount;
    } else {
      monthData.expense += t.amount;
    }
    monthlyStats.set(month, monthData);

    // 分类
    if (t.category && t.direction === "out") {
      const current = categoryStats.get(t.category) || 0;
      categoryStats.set(t.category, current + t.amount);
    }

    // 来源
    const currentSource = sourceStats.get(t.source) || 0;
    sourceStats.set(t.source, currentSource + t.amount);
  }

  // 格式化输出
  const lines: string[] = [];
  
  lines.push(`总交易笔数: ${transactions.length}`);
  lines.push("");
  
  lines.push("月度收支统计:");
  for (const [month, stats] of Array.from(monthlyStats.entries()).sort()) {
    lines.push(`  ${month}: 收入 ${stats.income.toFixed(2)}, 支出 ${stats.expense.toFixed(2)}`);
  }
  lines.push("");
  
  if (categoryStats.size > 0) {
    lines.push("支出分类统计（前10）:");
    const sortedCategories = Array.from(categoryStats.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    for (const [category, amount] of sortedCategories) {
      lines.push(`  ${category}: ${amount.toFixed(2)}`);
    }
    lines.push("");
  }
  
  lines.push("来源统计:");
  for (const [source, amount] of sourceStats.entries()) {
    const sourceName = source === "alipay" ? "支付宝" : source === "ccb" ? "建设银行" : "招商银行";
    lines.push(`  ${sourceName}: ${amount.toFixed(2)}`);
  }

  return lines.join("\n");
}
