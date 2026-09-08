---
phase: 04-m3-guards
plan: 02
subsystem: bash-guard
tags: [regex-blacklist, pretooluse, maint, guard-04]
provides:
  - zone _check-guard bash（bash_block_patterns 逐条 re.search；判区共用 _guard_resolve_zone）
  - hooks/pre_tool_use_bash.py（deny 话术 §8.2 原文）
affects: []
actuals:
  tokens: ~8000
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [check-guard action 分发重构（write/bash 共框架）]
key-files:
  created: []
  modified: [bin/zone, hooks/pre_tool_use_bash.py]
key-decisions:
  - "坏正则跳过该条不崩（doctor 范围）"
  - "七条正则的固有精度边界（git clean -Xfd / 多空格字面量）遵 DESIGN §8.2 原文不改——收紧属覆盖层选项，不在 plan 范围"
duration: 8min
completed: 2026-09-08
status: complete
---

# Phase 4 (M3) Plan 04-02 Summary

**Bash 护栏落地：十用例独立复测全过（GUARD-04 force-with-lease 精确放行）。**

## Performance

- **Duration:** ~8 min
- **Tasks:** 1/1
- **Files:** bin/zone+hooks 2 files +124/-23

## Accomplishments

- 十用例矩阵：7 deny / force-with-lease allow / status allow / core allow（主会话独立复测）
- 真会话验收：discuss 会话写文件被 PreToolUse 拦截，拒绝话术精确 §8；handoff 白名单路径放行（文件成功落盘）

## Task Commits

1. **全部** - `0768fb5`

## Decisions & Deviations

- 见 frontmatter key-decisions（正则精度边界遵循设计原文）

## Next Phase Readiness

- Phase 4 两 plan 齐备 → verify
