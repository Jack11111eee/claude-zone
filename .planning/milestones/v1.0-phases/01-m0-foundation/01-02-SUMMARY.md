---
phase: 01-m0-foundation
plan: 02
subsystem: session-start-hook
tags: [hooks, thin-wrapper, sessionstart, m-5]
provides:
  - hooks/session_start.py 实装（42 行薄封装）：L-1 subagent 跳过、startup-only 登记、区就绪提示行
  - SessionStart → zone _register-session 接线（M-5 首个完整落地）
affects: [02-m1-injection, 03-m2-handoff]
actuals:
  tokens: ~5000
  tasks: 2
  commits: 1
tech-stack:
  added: []
  patterns: [hook 薄封装（业务在 bin，hook 只组织输入输出）]
key-files:
  created: []
  modified: [hooks/session_start.py]
key-decisions:
  - "stdin source(startup/resume 枚举) 与索引 source(prefix/command 枚举) 是两套语义——hook 透传时重写为 prefix，防污染 §7.2 事件 schema"
  - "subprocess 失败静默 exit 0（degrade-to-open，launch 语境不炸会话）"
duration: 8min
completed: 2026-09-08
status: complete
---

# Phase 1 (M0) Plan 01-02 Summary

**SessionStart hook 薄封装落地，五向验收（前缀/无前缀/subagent/非startup/旧语法）全过。**

## Performance

- **Duration:** ~8 min
- **Tasks:** 2/2
- **Files:** hooks/session_start.py（42 行）

## Accomplishments

- 主路径闭环：`--core x` → 索引登记（source: prefix）→ stdout `核心区已就绪。`
- unzoned 零打扰（零输出、零事件）；subagent（L-1）与 resume/clear/compact 均静默跳过
- `[core] 旧` 自动归一化登记
- hooks.json 无需改动（session_start.py 下划线命名与 PLAN 的连字符写法不符，以磁盘为准）

## Task Commits

1. **全部** - `a635b0a`

## Files Created/Modified

- `hooks/session_start.py` - stub → 42 行实现

## Decisions & Deviations

- **source 双枚举重写**（stdin startup → 索引 prefix）：正确裁决，§7.2 语义保持
- subprocess 失败静默 exit 0：launch 语境 degrade-to-open，与 §9 护栏哲学同构

## Next Phase Readiness

- 02-02（UserPromptSubmit）可复用同构模式（stdin 解析 + subprocess 调 bin + JSON 消费）
- M0 验收仅差真会话端到端（留给 phase verify）
