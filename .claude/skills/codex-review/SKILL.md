---
name: codex-review
description: 使用本地 Codex CLI（codex exec）对当前仓库改动做只读代码审查；当用户提到"codex review/审查改动/检查本次会话修改"时使用。
---

# Codex Review（本地代码审查）

## 使用说明

当用户请求进行代码审查时，执行以下命令：

```bash
codex exec "Please review my uncommitted changes"
```

## 注意事项

- 只做审查，不修改文件
- 需要确保当前目录是 Git 仓库
- 需要确保已安装并配置好 Codex CLI
- 如果 codex 命令不可用，提示用户安装并登录
