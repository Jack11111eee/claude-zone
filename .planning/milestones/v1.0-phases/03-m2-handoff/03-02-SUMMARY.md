---
phase: 03-m2-handoff
plan: 02
subsystem: pending-query
tags: [dual-source, orphan, stale, h-3]
provides:
  - zone pending（目录扫描∩索引状态：孤儿 unregistered、consumed 排除、幽灵不出行）
  - zone list handoff 全量视图（含 consumed，幽灵如实列索引现值加 (ghost) 标注）
  - stale 渲染派生（created+14d，不写事件）
  - 全局 --json 归一化修复（argparse 双 parents 同 dest 怪癖——01-03 起从未生效过）
affects: [03-m2-handoff, 06-m5-review]
actuals:
  tokens: ~9500
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [双源真值：目录答存在性、索引答生命周期]
key-files:
  created: []
  modified: [bin/zone]
key-decisions:
  - "孤儿不自动登记（H-3 机器不猜状态；AST 验证 pending 路径全 read-only）"
  - "幽灵在 list 显示+ (ghost) 标注、pending 不显示（PLAN 未明说，按 §5 巡视语义最小合理实现）"
  - "全局前置 --json 修复（行为改进ніxel，此前所有子命令的该形态都是静默 no-op）"
duration: 20min
completed: 2026-09-08
status: complete
---

# Phase 3 (M2) Plan 03-02 Summary

**pending 双源查询落地：孤儿/排除/隔离/全量四视图独立复测通过。**

## Performance

- **Duration:** ~20 min
- **Tasks:** 1/1
- **Files:** bin/zone +235/-31

## Accomplishments

- pending 真值=目录∩索引（2 正常+孤儿 unregistered，consumed 排除）
- --zone=discuss 隔离正确；list handoff 段含 consumed 全量
- 注入联动：inject 后 pending 消失

## Task Commits

1. **全部** - `3014140`

## Decisions & Deviations

- 全局 --json 归一化修复（见 key-decisions）
- PLAN verify 行数差异按父指令定案（stale 行也列出）

## Next Phase Readiness

- 03-03 doctor 三类一致性检查的孤儿数据源与 pending 同构
