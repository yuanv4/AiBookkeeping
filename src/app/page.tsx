import Link from "next/link";
import { Upload, BarChart3, FileSpreadsheet, ArrowRight } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";

const BILL_FORMATS = [
  { name: "支付宝", format: "CSV", color: "bg-primary" },
  { name: "建设银行", format: "XLS", color: "bg-chart-3" },
  { name: "招商银行", format: "PDF", color: "bg-accent" },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <AppShell contentClassName="p-0">
          {/* Hero 区域 */}
          <section className="relative overflow-hidden">
            {/* 背景装饰 */}
            <div className="absolute inset-0 -z-10">
              <div className="absolute -top-12 -left-10 w-72 h-72 bg-primary/15 rounded-full blur-3xl opacity-80 animate-float"></div>
              <div className="absolute top-12 -right-10 w-80 h-80 bg-accent/15 rounded-full blur-3xl opacity-70 animate-float" style={{ animationDelay: "1.5s" }}></div>
              <div className="absolute -bottom-16 left-24 w-72 h-72 bg-chart-3/15 rounded-full blur-3xl opacity-70 animate-float" style={{ animationDelay: "3s" }}></div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-24">
              <div className="max-w-3xl">
                <h1 className="text-5xl md:text-6xl font-semibold tracking-tight mb-6 animate-fade-in text-balance">
                  多源账单，
                  <span className="bg-gradient-to-r from-primary via-chart-4 to-accent bg-clip-text text-transparent">
                    智能合一
                  </span>
                </h1>
                <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-12 animate-slide-up" style={{ animationDelay: "0.2s" }}>
                  支持支付宝、建设银行、招商银行等多种账单格式导入，
                  自动解析并统一管理，AI 驱动的可视化图表生成
                </p>
                <div className="flex flex-wrap items-center gap-4 animate-slide-up" style={{ animationDelay: "0.4s" }}>
                  <Link
                    href="/import"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 transition-colors shadow-sm"
                  >
                    开始导入 <ArrowRight className="w-4 h-4" />
                  </Link>
                  <Link
                    href="/ledger"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-secondary text-secondary-foreground rounded-full font-medium hover:bg-secondary/80 transition-colors"
                  >
                    查看账单
                  </Link>
                </div>
              </div>
            </div>
          </section>

          {/* 功能卡片 */}
          <section className="max-w-7xl mx-auto px-6 py-16">
            <div className="grid md:grid-cols-3 gap-6 animate-stagger">
              {/* 导入账单 */}
              <Link href="/import" className="group">
                <div className="p-6 rounded-2xl border border-border/80 bg-card/80 shadow-sm hover:shadow-md hover:border-primary/50 transition-all duration-300 h-full">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                    <Upload className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">导入账单</h3>
                  <p className="text-muted-foreground text-sm">
                    支持 CSV、XLS、PDF 格式，自动识别支付宝、建行、招行账单，
                    智能映射字段并预览解析结果
                  </p>
                </div>
              </Link>

              {/* 统一账单 */}
              <Link href="/ledger" className="group">
                <div className="p-6 rounded-2xl border border-border/80 bg-card/80 shadow-sm hover:shadow-md hover:border-accent/50 transition-all duration-300 h-full">
                  <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                    <FileSpreadsheet className="w-6 h-6 text-accent" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">统一账单</h3>
                  <p className="text-muted-foreground text-sm">
                    所有来源账单统一存储，支持按时间、来源、金额筛选，
                    快速搜索定位交易记录
                  </p>
                </div>
              </Link>

              {/* 图表分析 */}
              <Link href="/charts" className="group">
                <div className="p-6 rounded-2xl border border-border/80 bg-card/80 shadow-sm hover:shadow-md hover:border-chart-2/50 transition-all duration-300 h-full">
                  <div className="w-12 h-12 rounded-xl bg-chart-2/10 flex items-center justify-center mb-4 group-hover:bg-chart-2/20 transition-colors">
                    <BarChart3 className="w-6 h-6 text-chart-2" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">AI 图表分析</h3>
                  <p className="text-muted-foreground text-sm">
                    输入自然语言提示词，AI 自动生成 ECharts 图表，
                    支持折线图、柱状图、饼图等多种可视化
                  </p>
                </div>
              </Link>
            </div>
          </section>

          {/* 支持的格式 */}
          <section className="max-w-7xl mx-auto px-6 py-16 border-t border-border/70">
            <h2 className="text-2xl font-semibold text-center mb-8">支持的账单格式</h2>
            <div className="flex flex-wrap justify-center gap-4">
              {BILL_FORMATS.map((item) => (
                <div
                  key={item.name}
                  className="flex items-center gap-3 px-4 py-2 rounded-full bg-card/80 border border-border/70 shadow-sm"
                >
                  <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                  <span className="font-medium">{item.name}</span>
                  <span className="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded-full">
                    {item.format}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* 页脚 */}
          <footer className="border-t border-border/70 bg-background/60">
            <div className="max-w-7xl mx-auto px-6 py-8 text-center text-muted-foreground text-sm">
              <p>AI 智能记账 - 统一账单管理与可视化分析平台</p>
            </div>
          </footer>
      </AppShell>
    </main>
  );
}
