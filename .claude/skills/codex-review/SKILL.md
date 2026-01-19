---
name: codex-review
description: 使用本地 Codex CLI（codex exec）对当前仓库变更做代码审查（无需 GitHub/PR）。当用户说“用 codex review/审查这次改动/检查本次会话修改/看看 staged 或未提交改动”时使用。
allowed-tools: Bash Read Grep Glob
---

# Codex Review（本地审查，无需 GitHub）

## 目标
当用户希望对“本次会话的修改”进行审查时，调用本地 **Codex CLI** 完成 review，并把结果返回给用户：
- 默认审查：**未提交改动（unstaged）+ 已暂存改动（staged）**
- 可选审查：指定 commit、指定 base 分支对比、仅 staged、仅 unstaged

> 重要：本 Skill **只做审查，不修改文件**。如果用户要求修复，再单独征求确认后进行修改。

## 前置检查
1. 先检查当前目录是否是 Git 仓库（存在 `.git/`）。
2. 检查 `codex` 命令是否可用：
   - 若不可用：提示用户先安装/登录 Codex CLI（但不要中断主流程；给出明确的安装命令）。
3. 若仓库改动巨大（diff 很大/文件非常多），先在输出里提醒“建议拆分提交/分批 review”。

## 执行流程（必须按顺序）
1. 询问/判断用户想 review 的范围（尽量从用户话里推断，不要反复追问）：
   - “本次会话/当前改动/还没提交” => `uncommitted`
   - “staged/已暂存” => `staged`
   - “某个提交/上一次提交” => `commit:<sha or HEAD>`
   - “对比 main/dev” => `base:<branch>`
2. 调用脚本执行（优先用脚本，减少上下文占用）：
   - `scripts/codex_review.sh <mode>`
3. 把脚本输出原样展示给用户，并额外补一段“下一步建议”（例如：需要补测试/可疑边界条件/潜在安全风险）。

## 输出格式（强制）
用 Markdown 输出，结构固定：
- **Summary（3~6 条）**：最关键问题优先
- **High risk**：可能导致 bug/安全/数据损坏的点
- **Correctness**：逻辑/边界/并发/错误处理
- **Security & Privacy**：密钥/注入/权限/日志泄漏
- **Performance**：复杂度/热点路径/不必要 IO
- **Maintainability**：可读性/重复/命名/结构
- **Tests**：缺哪些测试，用例要点
- **Nitpicks（可选）**：低优先级格式建议

## 安全约束（必须遵守）
- 不要把 `.env`、密钥、token、证书、私钥内容复制到提示词或输出中。
- 默认只 review “用户本次变更相关的文件”；不要遍历无关内容。
- 如果用户明确要求“只读审查”，严格禁止写入/修改任何文件。
