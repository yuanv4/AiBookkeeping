---
name: ccommit
description: 按照 Conventional Commits 规范生成并执行 git commit
---

# Conventional Commits 提交

按照 Conventional Commits 规范自动生成并执行 git commit。

## 执行步骤

1. **获取暂存区改动**
   运行 `git diff --cached` 查看暂存区的所有改动

2. **分析改动内容**
   严谨分析代码改动的类型、范围和目的

3. **生成提交信息**
   严格遵循 Conventional Commits 规范:
   ```
   <type>(<scope>): <description>

   <body>(可选)

   <footer>(可选)
   ```

   **type(必选)**: 改动类型
   - `feat`: 新功能
   - `fix`: 修复 bug
   - `docs`: 文档改动
   - `style`: 代码格式(不影响代码运行)
   - `refactor`: 重构(既不是新增功能,也不是修复 bug)
   - `perf`: 性能优化
   - `test`: 增加测试
   - `build`: 构建系统或外部依赖的变动
   - `ci`: CI 配置文件和脚本的变动
   - `chore`: 其他不修改 src 或 test 文件的改动
   - `revert`: 回退之前的 commit

   **scope(可选)**: 改动范围,如: auth, api, ui, database 等

   **description(必选)**: 简短描述,使用中文说明改动的具体内容

4. **执行提交**
   使用生成的提交信息执行 git commit 命令

5. **添加签名**
   在提交信息末尾添加标准的签名信息:
   ```
   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   ```

## 示例

```
feat(auth): 添加用户登录功能

- 实现用户名密码登录
- 添加 JWT token 认证
- 新增登录表单验证

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
