---
phase: 03-m2-handoff
plan: 01
subsystem: handoff-lifecycle
tags: [frontmatter, register, inject, event-sourcing]
provides:
  - 受限 frontmatter 解析（flat 键值+tags 列表，复用 02-01 标量语法）
  - zone register（五段校验：存在/防跨项目 realpath/字段值域/id 正则；幂等 already；title 取 # 一级标题）
  - zone inject（--session/CLAUDE_CODE_SESSION_ID、consumed �拒 exit 3、--force re_consumed subtype "inject --force"、幽灵 exit 3）
affects: [03-m2-handoff, 05-m4-chains]
actuals:
  tokens: ~12000
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [写入=登记原子（register 只读文档+append 索引，无移动）]
key-files:
  created: []
  modified: [bin/zone]
key-decisions:
  - "幂等 register exit 0 + stderr 提示（重复是安全 no-op）"
  - "缺 session 前置于查索引（无 session 恒 exit 2）"
duration: 10min
completed: 2026-09-08
status: complete
---

# Phase 3 (M2) Plan 03-01 Summary

**handoff 生命周期引擎落地：register 校验链与 inject 三态全部独立复测通过。**

## Performance

- **Duration:** ~10 min
- **Tasks:** 2/2
- **Files:** bin/zone +294

## Accomplishments

- register 五段校验（含防跨项目 realpath 前缀）+ 幂等 + title 抽取
- inject 生命周期：pending→consumed（by 记录）→re_consumed（--force）；拒绝话术含 P-4 出处
- 9+ 边界用例（id 形态/to:unzoned 拒/幽灵/缺 session/跨区消费 B-1）

## Task Commits

1. **全部** - `f46b59a`

## Decisions & Deviations

- 见 frontmatter key-decisions（幂等语义、session 前置）

## Next Phase Readiness

- 03-02 pending 双源的目录扫描可直接复用 handoffs_dir() 辅助
