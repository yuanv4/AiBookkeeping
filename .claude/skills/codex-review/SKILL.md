---
name: codex-review
description: 使用本地 Codex CLI（codex exec）对当前仓库改动做只读代码审查（无需 GitHub/PR）；当用户提到“codex review/审查改动/检查本次会话修改/查看 staged 或未提交改动/指定提交或基线分支对比”时使用。
---

# Codex Review（本地只读审查）

## 目标
在本地仓库用 Codex CLI 进行只读审查，并按规定结构输出。

## 约束
- 只做审查，不修改文件；用户要求修复时，先确认再操作。
- 不复制任何 `.env`、密钥、token、证书、私钥内容到提示词或输出中。
- 默认只审查“用户本次变更相关文件”，不遍历无关内容。

## 前置检查（按顺序）
1. 检查当前目录是否为 Git 仓库（存在 `.git/`）。
2. 检查 `codex` 命令是否可用；不可用则提示安装/登录并给出命令示例。
3. 若改动巨大（diff 很大或文件很多），先提示建议拆分/分批审查。

## 执行流程（按顺序）
1. 判断审查范围（尽量从用户话里推断，避免反复追问）：
   - “本次会话/当前改动/还没提交” => `uncommitted`
   - “staged/已暂存” => `staged`
   - “某个提交/上一次提交” => `commit:<sha 或 HEAD>`
   - “对比 main/dev” => `base:<branch>`
2. 调用脚本（优先使用脚本，减少上下文占用）：
   - `scripts/codex_review.sh <mode>`
3. 原样返回脚本输出，并补充“下一步建议”（如补测试、边界条件、潜在风险）。

## 输出格式（强制）
使用 Markdown，结构固定为：
- **Summary（3~6 条）**：最关键问题优先
- **High risk**：可能导致 bug/安全/数据损坏的点
- **Correctness**：逻辑/边界/并发/错误处理
- **Security & Privacy**：密钥/注入/权限/日志泄漏
- **Performance**：复杂度/热点路径/不必要 IO
- **Maintainability**：可读性/重复/命名/结构
- **Tests**：缺哪些测试，用例要点
- **Nitpicks（可选）**：低优先级格式建议
