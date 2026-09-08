---
phase: 09-guard-hardening
plan: 01
subsystem: guard
tags: [regex-hardening, test-matrix, git-s-prefix]
provides:
  - zones/maint.yaml 七条正则 git\s+ 前缀统一 + clean 组合旗标收紧
  - tests/test_guard_hardening.py（24 断言可重跑矩阵）
affects: [zones/maint.yaml, tests/]
actuals:
  tokens: ~4500 subagent + ~2000 主会话复测
  tasks: 3
  commits: 1 (913a23f)
tech-stack:
  added: []
  patterns: [护栏形态学在 yaml 数据层收敛（bin re.search 逻辑零改动）]
key-files:
  created: [tests/test_guard_hardening.py]
  modified: [zones/maint.yaml]
key-decisions:
  - "clean 收紧为 -[a-zA-Z]*f：字母组合旗标含 f 即拦（git clean 的 f 永远意味着删文件），-n 干跑不受误伤"
  - "七条统一 git\\s+ 前缀（含 push/reset/branch/checkout/reflog/gc）——一次规律而非逐条补丁"
duration: 39min subagent + 10min 复测
completed: 2026-09-08
status: complete
---

# Phase 9 Plan 09-01 Summary

**护栏加固：三组矩阵 24 断言全绿 + 真会话 maint 拦截实证。bin 逻辑零改动（正则纯数据层）。**

## Performance

- **Duration:** 子代理 ~39 min + 主会话复测 ~10 min
- **Tasks:** 3/3

## Accomplishments

- 实测绕过根除：`git clean -Xfd`/`-xfd`/`-Xf`/`-fx`/双空格全家（含 `git  clean -Xfd` 交叉）全 deny
- `--force(?!\S)` 负向前瞻保留：`--force-with-lease` 放行（GUARD-04 锚点）；`git clean -n` 干跑放行
- tests/test_guard_hardening.py 首个入库测试（repo 原无 tests/；纯 stdlib + 真子进程调 bin + ZONING_HOME 隔离）

## 发现

- 测试基建坑：macOS TMPDIR 是 `/var` symlink → 两侧 slug 不一致假阴性；修法 realpath 统一（子代理在测试脚本内解决，真实 hook 链路无此问题）
- DESIGN.md §8.2 旧正则快照未同步（plan 外文件，纪律不动；Phase 10 可顺手）

## Verification（主会话独立复测）

- 子代理矩阵脚本主会话重跑：24 passed, 0 failed
- 独立 hook 链路七形态（不经测试脚本直跑 pre_tool_use_bash.py）行为正确：三 new-form deny、lease allow、`git clean -n` allow
- **真会话**：`claude -n "--maint P9护栏复测" -p` 令其执行 `git clean -Xfd` → 被拒，理由 §8 原文，模型并主动建议 `git clean -Xnd` 干跑安全形态
