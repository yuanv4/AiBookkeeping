---
name: conventional-commit
description: 分析暂存区改动，按 Conventional Commits（约定式提交）生成并执行 git commit；当用户要求提交或需要规范化提交信息时使用。
---

## 目标
1. 准确理解暂存区改动的用户可见影响与范围。
2. 输出严格符合 Conventional Commits 的提交信息。
3. 在用户明确要求时执行 `git commit`。

## 工作流程
1. 检查暂存区改动（仅针对已暂存内容）。
2. 归纳改动类型、影响范围与是否破坏性变更。
3. 生成提交信息（必要时包含正文与 Footer）。
4. 若用户要求执行提交，再运行 `git commit`。

## 规则
- 标题格式：`<type>(<scope>): <description>`，其中 `<scope>` 可省略。
- `type` 仅限：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore`、`revert`。
- 标题用祈使语气，简洁明确，避免句号，长度不超过 72 个字符。
- 破坏性变更：在标题类型后加 `!`，或在 Footer 写 `BREAKING CHANGE:`。
- `scope` 选择优先级：用户影响最大模块 > 改动最多模块 > 最核心模块。
- 仅重排/格式化/空白调整用 `style`；不改变行为的结构调整用 `refactor`。
- `docs` 只用于文档或注释变更；`chore` 用于杂项、工具或依赖更新。

## 正文与 Footer
- 正文用于说明动机、背景、关键实现与潜在副作用。
- Footer 用于关联 issue、破坏性变更说明或迁移提示。

## 示例
- `feat(charts): add stacked bar export`
- `fix(auth): handle token refresh race`
- `docs: update api usage`
- `refactor(core)!: simplify cache lifecycle`
- `revert: revert "feat(api): add webhook retries"`

## 边界情况
- 暂存区为空：提示用户先暂存改动或说明无法提交。
- 改动跨多个领域：优先选取影响最大的 `scope`，必要时在正文补充其余范围。
