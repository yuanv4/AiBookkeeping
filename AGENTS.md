# AGENTS.md

## 一、项目概述

账单汇总项目：聚合多数据源交易流水，完成清洗、归类、对账，服务分析与报表。  
项目为个人维护，**禁止工程化**，避免过度设计与复杂架构。

## 二、语言与文档

- 代码标识符（变量/函数/类名）遵循最佳实践，使用英文
- 技术配置文件（JSON/YAML/TOML/CI 等），使用英文
- 仅在以下情况使用中文：
  - 全部对话、文档、说明、注释使用中文（简体）
  - 用户明确要求
  
## 三、编码规范

- **遵循 KISS**，优先简洁直观的实现

## 四、测试规范

- 测试框架：Vitest
- 测试脚本目录：src/__tests__/
- 优先写 API 集成测试，避免浏览器端 E2E

## 五、子代理

使用 Task 工具调用：

- **code-simplifier**：代码简化与重构  
  触发：用户说“调用code-simplifier”或要求优化代码  
  配置：.claude/agents/code-simplifier.md
<!--
- **codex-review**：代码质量审查  
  触发：用户说“调用codex-review”或要求审查代码  
  配置：.claude/agents/codex-review.md
-->
