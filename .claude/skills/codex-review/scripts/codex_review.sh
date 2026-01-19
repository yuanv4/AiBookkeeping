#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-uncommitted}"

# --- helpers ---
say() { printf "%s\n" "$*"; }
die() { say "ERROR: $*"; exit 1; }

# Ensure git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "当前目录不是 Git 仓库（找不到 .git）。请在仓库根目录运行。"

# Ensure codex exists
if ! command -v codex >/dev/null 2>&1; then
  say "未检测到 codex CLI。请先安装并登录（示例）："
  say "  npm i -g @openai/codex"
  say "  codex"
  die "codex 不可用，无法执行 review。"
fi

# Build prompt for codex exec (read-only review)
BASE_BRANCH=""
COMMIT_REF=""

case "$MODE" in
  uncommitted)
    ;;
  staged)
    ;;
  commit:*)
    COMMIT_REF="${MODE#commit:}"
    ;;
  base:*)
    BASE_BRANCH="${MODE#base:}"
    ;;
  *)
    die "未知模式：$MODE。支持：uncommitted | staged | commit:<sha|HEAD> | base:<branch>"
    ;;
esac

# A concise, strict review instruction for Codex.
# We ask Codex to run git commands itself to fetch diffs; avoid embedding diffs here.
PROMPT_COMMON=$'You are doing a READ-ONLY code review in the current git repository.\n- DO NOT modify any files.\n- DO NOT run destructive commands.\n- You MAY run: git status, git diff, git show, git log, tests in read-only mode (no writes).\n- Focus on: correctness, security/privacy, edge cases, and missing tests.\n- Output Markdown with sections: Summary, High risk, Correctness, Security & Privacy, Performance, Maintainability, Tests, (optional) Nitpicks.\n- Keep it actionable and prioritized.\n'

if [[ -n "$COMMIT_REF" ]]; then
  PROMPT="$PROMPT_COMMON"$'\nReview target:\n- Review ONLY this commit: '"$COMMIT_REF"$'\nSteps:\n1) Run: git show --stat '"$COMMIT_REF"$'\n2) Run: git show '"$COMMIT_REF"$'\n3) Produce the review.\n'
elif [[ -n "$BASE_BRANCH" ]]; then
  PROMPT="$PROMPT_COMMON"$'\nReview target:\n- Compare current HEAD against base branch: '"$BASE_BRANCH"$'\nSteps:\n1) Run: git fetch --all --prune (safe)\n2) Find merge base and diff: git diff '"$BASE_BRANCH"'...HEAD\n3) Also check status: git status\n4) Produce the review.\n'
else
  if [[ "$MODE" == "staged" ]]; then
    PROMPT="$PROMPT_COMMON"$'\nReview target:\n- Review STAGED changes only.\nSteps:\n1) Run: git status\n2) Run: git diff --staged\n3) Produce the review.\n'
  else
    PROMPT="$PROMPT_COMMON"$'\nReview target:\n- Review this session changes (UNSTAGED + STAGED).\nSteps:\n1) Run: git status\n2) Run: git diff\n3) Run: git diff --staged\n4) Produce ONE consolidated review.\n'
  fi
fi

# Run codex in non-interactive mode
# Note: codex exec supports scripted runs.
codex exec "$PROMPT"
