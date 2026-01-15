---
name: conventional-commit
description: >
  Generate and validate git commit messages using the Conventional Commits specification.
  This skill MUST be used whenever a git commit is created.
---

# Instructions

When a git commit is about to be created:

1. Analyze the diff to determine:
   - type (feat, fix, docs, refactor, chore, etc.)
   - optional scope
   - concise subject in imperative mood

2. Generate a commit message strictly following:
   <type>(<scope>): <subject>

3. Enforce rules:
   - subject ≤ 72 characters
   - no trailing period
   - imperative mood
   - lowercase type and scope

4. If the message does not comply:
   - rewrite it
   - do NOT proceed with commit using a non-compliant message

5. Prefer correctness over brevity.
