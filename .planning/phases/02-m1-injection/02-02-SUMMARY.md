---
phase: 02-m1-injection
plan: 02
subsystem: prompt-injection
tags: [additionalContext, userpromptsubmit, zone-switch, skill-placeholder]
provides:
  - zone _zone-prompt（prompt 单一来源，经 load_zone_def 合并管线）
  - zone _zap-title（transcript 首条消息取名 40 字/日戳 fallback/归一化/source:command 登记）
  - SessionStart additionalContext 注入（提示行折进 context 首行，stdout 保持纯 JSON）
  - UserPromptSubmit hook（/zone 换区全套）+ skills/zone/SKILL.md 占位（V-5 前提）
affects: [03-m2-handoff, 04-m3-guards]
actuals:
  tokens: ~9000
  tasks: 3
  commits: 1
tech-stack:
  added: []
  patterns: [additionalContext 双事件注入（SessionStart 建身份 + UserPromptSubmit 补身份）]
key-files:
  created: [skills/zone/SKILL.md]
  modified: [bin/zone, hooks/session_start.py, hooks/user_prompt_submit.py]
key-decisions:
  - "_zone-prompt 未知区 exit 4 非 2（§5 '定义非法' 与 P-6 一致，覆盖派发指令笔误）"
  - "提示行折进 additionalContext 首行——stdout 必须纯 JSON 才被解析为注入（人类可读与机器可读不能共存于 stdout）"
  - "_ZONE_PROMPT_RE 用 $ 精确锚定（\s*$ 会吞 /zone inject 参数——执行中自查修复）"
duration: 14min
completed: 2026-09-08
status: complete
---

# Phase 2 (M1) Plan 02-02 Summary

**区身份注入双通道落地：主路径 SessionStart 与补救 /zone 全部真会话实证。**

## Performance

- **Duration:** ~14 min
- **Tasks:** 3/3
- **Files:** 4 files +227

## Accomplishments

- 真会话 `--discuss` 会话模型亲证 zone prompt 注入（SessionStart additional context）
- 真会话 `/zone maint` 换区：索引 source:command 事件 + title 日戳 fallback + 模型确认进入维护区
- 普通消息/inject 形态/带说明的 /zone 均静默（精确匹配设计）

## Task Commits

1. **全部** - `2eadf5a`

## Files Created/Modified

- `bin/zone` - _zone-prompt/_zap-title
- `hooks/session_start.py` - additionalContext 注入（59 行）
- `hooks/user_prompt_submit.py` - /zone 换区（61 行）
- `skills/zone/SKILL.md` - 占位

## Decisions & Deviations

- exit 4 裁决、$ 锚定修复、transcript_path 缺失 fallback（详见 frontmatter key-decisions）

## Next Phase Readiness

- 03-04 的 pending 探测提示行可直接挂在两 hook 已留的扩展点上
- Phase 4 判区逻辑（by sessionId）与 _zap-title 的登记同源
