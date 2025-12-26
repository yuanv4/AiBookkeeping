---
description: 按照 Conventional Commits 规范生成并执行 git commit
---

## Context
- Staged changes: !`git diff --cached`

## Task
1. 严谨分析暂存区的代码改动。
2. 严格遵循 Conventional Commits 规范生成提交信息。
3. 格式：<type>(<scope>): <description>。
4. 类型限制：feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert。