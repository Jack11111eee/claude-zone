---
phase: 07-consolidation
plan: 01
subsystem: consolidation
tags: [single-source, labels-retirement, display-field]
provides:
  - bin/zone zone_display_text + _zone-prompt/_check-guard display 字段
  - hooks 三文件 LABELS 退役，文案单源化
affects: [bin/zone, hooks/session_start.py, hooks/user_prompt_submit.py, hooks/pre_tool_use_write.py]
actuals:
  tokens: ~3000 subagent + ~1500 主会话复测
  tasks: 4
  commits: 1 (73034bd)
tech-stack:
  added: []
  patterns: [文案字段随数据命令走（display 附 _zone-prompt 响应，零额外 subprocess）]
key-files:
  created: []
  modified: [bin/zone, hooks/session_start.py, hooks/user_prompt_submit.py, hooks/pre_tool_use_write.py]
key-decisions:
  - "pre_tool_use_write 的 display 走 _check-guard 输出扩展而非另起子命令——六输出点 deny/allow 同构，unzoned null"
  - "display 缺失 fallback zone 原名（degrade-to-open：文案缺失不产生新失败路径）"
duration: 32min subagent + 10min 复测
completed: 2026-09-08
status: complete
---

# Phase 7 Plan 07-01 Summary

**LABELS 退役完成：四处 hook 文案从 zones/*.yaml display 单源派生，行为零回归（真会话复测全绿）。**

## Performance

- **Duration:** 子代理 ~32 min + 主会话独立复测 ~10 min
- **Tasks:** 4/4
- **Files:** bin/zone（+61 行）、hooks ×3

## Accomplishments

- `zone_display_text` 与 prompt 同管线同校验形状；`_zone-prompt` data 扩 display（旧 key 原位不动）
- `_check-guard` 六输出点全带 display（写/bash 双动作）；hook `label = display or zone`
- session_start 的 unzoned 判断从 `zone not in LABELS` 改为显式 `unzoned/None` 判断，语义等价且不再依赖词表存在
- 单源证明实测：overlay `display: 超核` → 「超核区已就绪。」，移除还原

## Verification（主会话独立复测）

- LABELS grep 零命中；四区 display 值对 yaml；`核心区已就绪。` 逐字回归
- 护栏矩阵：discuss deny 文案逐字同 v1.0、allow_paths 豁免静默、unzoned 静默
- **真会话**：`--core` 提示行「核心区已就绪。」；discuss 内 Write 被拒，模型复述理由并引导 /handoff 流程
- doctor problems: []
