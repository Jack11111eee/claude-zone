---
status: passed
phase: 01-m0-foundation
verified: 2026-09-08
requirements: [ZONE-01, ZONE-03, STORE-01]
method: goal-backward（真会话端到端 + 隔离单元测试 + 独立复测）
---

# Phase 1 Verification Report (M0 底座)

## Goal 对照

**Goal**: 插件骨架可用：`claude -n "--core x"` 起会话见提示行，`zone list` 出表，索引事件落盘

## 成功判据逐条核验

| # | 判据 | 结果 | 证据 |
|---|------|------|------|
| 1 | 插件脚手架就位（plugin.json、hooks.json、bin/zone 可执行） | ✅ | 本地 marketplace 安装 `zoning@zoning` 成功并即时生效（hook 实跑证明） |
| 2 | `claude -n "--core 测试"` 新会话：hook 解析前缀，index.jsonl 出现 session 事件（source: prefix），stdout 提示区就绪 | ✅ | 真会话（sessionId 28c24eb2…）事件行全字段合规：`{"v":1,"type":"session","zone":"core","title":"--core m0真实验收","source":"prefix"}`；隔离测试验证 stdout `核心区已就绪。` |
| 3 | 不带前缀的会话：零打扰 | ✅ | 真会话 `claude -n "无前缀的普通会话"` → 索引行数不变（1）、无提示行 |
| 4 | `zone which/list/title --json` 返回规范 JSON（附录 A 契约） | ✅ | which→core、list 表格+中文对齐、title 归一化（[core]→--core）、--json 含 ok/v/cmd/data |

## 实现内验收（隔离测试补充）

- L-1 subagent 跳过：agent_type 存在 → 静默 ✅
- resume/compact 不登记（startup-only）✅
- 坏行容忍：手工注入非 JSON 行后 which/list 照常 ✅
- 双次登记语义：同 sessionId 后值即现值（事件溯源）✅
- 纯标准库：import 扫描无第三方 ✅
- hook 延迟预算：~140ms/调用（notes-hook-latency.md）✅

## 发现与修复（执行期）

1. maint.yaml push 正则 `--force` 会误伤 `--force-with-lease`（DESIGN §8.2 明言放行）→ 修正为 `--force(?!\S)`（H-2 深链精神的护栏精度问题）
2. YAML 双引号标量下 `\s` 非法转义导致解析失败 → 七条黑名单改单引号包裹
3. stdin source（startup 枚举）与索引 source（prefix 枚举）双语义 → hook 重写为 prefix

## 结论

**Phase 1 (M0) 通过。** 垂直切片第一片端到端成立：命名前缀 → hook → 索引 → 提示行，全链路机器层工作正常。v0.1 零件齐备。
