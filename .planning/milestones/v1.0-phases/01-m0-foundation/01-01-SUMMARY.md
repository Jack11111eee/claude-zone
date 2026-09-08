---
phase: 01-m0-foundation
plan: 01
subsystem: plugin-scaffold
tags: [python-stdlib, argparse, yaml, hooks-json, plugin-manifest]
provides:
  - 插件脚手架（.claude-plugin/plugin.json + hooks/hooks.json + 五个 hook stub）
  - bin/zone 骨架：argparse 全子命令声明 + title 实装（前缀解析/[zone] 归一化/unzoned 判定）
  - 附录 A --json 输出契约（全局旗标，子命令前）
  - zones/{chore,core,discuss,maint}.yaml 四区内置默认（guards 值 = H-1 表）
affects: [01-m0-foundation, 02-m1-injection, 03-m2-handoff, 04-m3-guards]
actuals:
  tokens: ~12000
  tasks: 3
  commits: 1
tech-stack:
  added: [python3 stdlib only]
  patterns: [单一 bin 宿主 + 薄 hook 封装（M-5）]
key-files:
  created: [bin/zone, .claude-plugin/plugin.json, hooks/hooks.json, hooks/*.py stubs, zones/*.yaml]
  modified: []
key-decisions:
  - "push 黑名单正则加负向前瞻 --force(?!\\S)：原始 --force 会误伤 --force-with-lease（DESIGN §8.2 L-6 注释明言放行）——执行中发现并修复"
duration: 12min
completed: 2026-09-08
status: complete
---

# Phase 1 (M0) Plan 01-01 Summary

**插件脚手架 + zone bin 基础落地，三个 task 全验收通过。**

## Performance

- **Duration:** ~12 min
- **Tasks:** 3/3
- **Files:** 15 created

## Accomplishments

- `zone title` 全行为：`--core 测试`→core；`[core] 旧`→归一化 core（normalized: true）；`普通`/`--nope x`→unzoned（四区封闭集合判定）
- hooks.json 五事件接线（SessionStart×1/UserPromptSubmit/PreToolUse×2/SessionEnd），全部 `$CLAUDE_PLUGIN_ROOT` 前缀
- 四区 yaml 与 §2.1 prompt 逐字一致，guards 值对齐 H-1 表

## Task Commits

1. **全部三 task** - `71f997a`

## Files Created/Modified

- `bin/zone` - 唯一可执行；argparse 骨架+title 实装+--json 契约；未实装子命令 exit 2
- `.claude-plugin/plugin.json` / `hooks/hooks.json` - 插件清单与事件声明
- `hooks/*_*.py ×5` - 占位 stub（01-02/01-03 填实）
- `zones/*.yaml ×4` - 四区定义

## Decisions & Deviations

- **修正**：§8.2 push 正则 `--force` → `--force(?!\S)`，否则 `git push --force-with-lease`（保护性操作，DESIGN 明言放行）会被误拦。已用 4 用例矩阵验证（force 拦/lease 放/-f 放——短旗标系另一形态 §8.2 未列，维持不拦/普通放行）。
- 子命令未实装即调用 → stderr not-implemented + exit 2（plan 内规定，无偏差）。

## Next Phase Readiness

- 01-03（wave 2）可直接开工：索引引擎+which/list/_register-session
- 01-02（wave 3）等 01-03 接口
