---
phase: 01-m0-foundation
plan: 03
subsystem: sidecar-index
tags: [python-stdlib, jsonl, event-sourcing, append-only]
provides:
  - 索引引擎：ZONING_HOME 覆盖、project slug、append-only 单行 jsonl、坏行容忍、事件重放（同 sessionId 末值即现值）
  - zone _register-session（M-5 薄封装的 bin 侧登记入口；stdin 字段名映射 session_id→sessionId）
  - zone which（--session 缺省读 CLAUDE_CODE_SESSION_ID，V-8 结论落地）
  - zone list（会话表 + handoff 表骨架；中文宽字符对齐；相对时间）
affects: [01-m0-foundation, 03-m2-handoff, 04-m3-guards]
actuals:
  tokens: ~14000
  tasks: 2
  commits: 1
tech-stack:
  added: [event replay]
  patterns: [事件溯源最小实现（不重写历史）]
key-files:
  created: []
  modified: [bin/zone]
key-decisions:
  - "ZONING_HOME 环境变量支持（测试隔离；不进文档契约）"
  - "stdin session_id（hook 实际字段）映射到事件 schema sessionId（§7.2 拼写）"
duration: 18min
completed: 2026-09-08
status: complete
---

# Phase 1 (M0) Plan 01-03 Summary

**sidecar 索引引擎落地：登记/重放/查询三面全验收（含坏行容忍与双次登记语义）。**

## Performance

- **Duration:** ~18 min
- **Tasks:** 2/2
- **Files:** bin/zone +378 行

## Accomplishments

- `zone _register-session`：stdin JSON→session 事件 append；unzoned 零动作；[zone] 归一化写回
- `zone which`：末值重放正确（core→discuss 同 session 双登记后 which=discuss）；CLAUDE_CODE_SESSION_ID 免参
- `zone list`：表格（中文宽字符对齐）+ --json items
- 坏行（手工注入非 JSON 行）：which/list 照常（跳过收集）
- 索引路径 `$ZONING_HOME/zoning/<slug>/index.jsonl`，slug 规则实测同 ~/.claude/projects

## Task Commits

1. **全部** - `1e10aa9`

## Files Created/Modified

- `bin/zone` - 索引模块（resolve_root/append_event/read_events/replay_sessions）+ which/list/_register-session

## Decisions & Deviations

- 空 sessionId 输入仍会写事件（sessionId:""）——真实 hook 场景 stdin 总有 session_id，边角可接受；后续 phase 若做防御再加非空校验
- 其余无偏差

## Next Phase Readiness

- 01-02 hook 的登记入口就绪（_register-session 接口已冻结）
- Phase 3 的 handoff 事件可复用 append_event/read_events
