---
phase: 03-m2-handoff
plan: 03
subsystem: doctor-consistency
tags: [orphan, ghost, misplaced, corrupt-line, l-2]
provides:
  - doctor 三类一致性检查（孤儿带修复指引/幽灵含 exit 3 预告/命名错位以 frontmatter 为准）
  - 索引坏行报告（read_events 的 skipped 扩为 {line, raw}）
  - consumed 幽灵豁免（文档可能被 gc/归档，不误报）
affects: [03-m2-handoff]
actuals:
  tokens: ~7500
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [_consistency_problems 单次扫描喂两类问题（孤儿+错位），索引侧出幽灵]
key-files:
  created: []
  modified: [bin/zone]
key-decisions:
  - "幽灵筛查含 re_consumed 不含 consumed（--force 会 exit 3 是实行为，别猜测 §7.4 未分态处）"
  - "一因一报：放错目录的文件算命名错位不算幽灵"
duration: 18min
completed: 2026-09-08
status: complete
---

# Phase 3 (M2) Plan 03-03 Summary

**doctor 一致性三查落地：孤儿/幽灵/坏行独立复测通过（23 项断言 + 主会话复测）。**

## Performance

- **Duration:** ~18 min
- **Tasks:** 1/1
- **Files:** bin/zone +84/-6

## Accomplishments

- 四问题场景矩阵（孤儿+幽灵+错位+坏行）全过；consumed 幽灵豁免正确
- 修复路径指引文案与 D-002（机器不猜状态）一致
- 回归：定义检查（B-6/P-6）不受影响；doctor 恒 exit 0

## Task Commits

1. **全部** - `ff90167`

## Decisions & Deviations

- 详见 frontmatter key-decisions（幽灵分态、一因一报）

## Next Phase Readiness

- 03-04 收口后 M2 全链路完成 = v0.1
