---
phase: 04-m3-guards
plan: 01
subsystem: write-guard
tags: [pretooluse, glob, carve-out, degrade-to-open]
provides:
  - zone _check-guard write（判区 by sessionId → deny_write_edit → allow_paths glob 豁免）
  - hooks/pre_tool_use_write.py（PreToolUse permissionDecision deny + 中文话术；guard 故障静默放行）
  - 自实现 glob（** 跨段 memo 回溯 / * 段内 / 裸模式 basename——防指数爆炸）
affects: [04-m3-guards]
actuals:
  tokens: ~14500
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [决策走数据不走退出码（hook 翻译层永不掉链）]
key-files:
  created: []
  modified: [bin/zone, hooks/pre_tool_use_write.py]
key-decisions:
  - "deny 话术单一模板+区名插值（maint 额外放行不靠话术说明——B-4 已在路径层表达）"
  - "guard 故障（bin 失败/坏输出）→ hook 静默放行：护栏永不因自身故障拦写作（degrade-to-open 哲学的 hook 侧延伸）"
duration: 19min
completed: 2026-09-08
status: complete
---

# Phase 4 (M3) Plan 04-01 Summary

**Write/Edit 护栏落地：六象限+glob 豁免矩阵全过（bin 与 hook 双侧）。**

## Performance

- **Duration:** ~19 min
- **Tasks:** 2/2
- **Files:** bin/zone +~120 行、pre_tool_use_write.py <60 行

## Accomplishments

- 独立复测六象限精确：discuss×src deny / discuss×handoffs allow / maint×.gitignore allow / maint×src deny / core allow / unzoned allow
- glob：**/handoffs/** 跨目录嵌套命中、handoffs2 不误中、**/.claude/zones/** 与裸 .gitignore basename 各就
- Q-4 覆盖层（repo yaml 翻 deny_write_edit）穿透求值正确

## Task Commits

1. **全部** - `adb0c2f`

## Decisions & Deviations

- 详见 frontmatter key-decisions

## Next Phase Readiness

- 04-02 Bash 护栏复用同构 _check-guard 框架（bash_block_patterns 替代 allow_paths）
