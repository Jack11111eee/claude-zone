---
status: passed
phase: 02-m1-injection
verified: 2026-09-08
requirements: [PROMPT-01, PROMPT-02, PROMPT-03, ZONE-02]
method: goal-backward（真会话端到端 ×3 + 隔离单元测试矩阵 + 独立复测）
---

# Phase 2 Verification Report (M1 注入)

## Goal 对照

**Goal**: 四区身份进会话：zone prompt 注入 + /zone 补救换区 + 提示（不注入）未消费 handoff

## 成功判据逐条核验

| # | 判据 | 结果 | 证据 |
|---|------|------|------|
| 1 | 主路径会话启动即见所在区 prompt，文本与 §2.1 定稿一致 | ✅ | 真会话 `claude -n "--discuss M1真实验收"`：模型亲证"讨论区已就绪+四区 prompt 全文"以 SessionStart hook additional context 注入；隔离测试 prompt 长度/逐字节与 `_zone-prompt` 输出一致 |
| 2 | 会话内 `/zone core`：title 补前缀、追加 source:command 事件、模型收到 zone prompt | ✅ | 真会话纯净 `/zone maint`：索引出现 `{"zone":"maint","title":"--maint 09-08","source":"command"}`（title 日戳 fallback 正确——首条消息是命令无文本）；模型回复确认已进维护区且复述了 zone 职责 |
| 3 | /zone 命令文件存在且为占位正文 | ✅ | skills/zone/SKILL.md 一行占位；真会话中命令展开可见（"本命令已由 hook 处理"） |
| 4 | 换区持续有效：档位随最后事件 | ✅ | 事件流重放语义（01-03 已验）+ /zone 后 which 取 command 事件 |
| 5 | ZONE-02 yaml 覆盖合并+未知字段报错 | ✅ | 02-01 验收（doctor 三态/深合并/第五区警告），PyYAML 值级对照 |

## 行为边界确认

- 普通消息 → UPS hook 静默（真会话与隔离测试双证）
- `/zone inject ho-1`（复杂参数形态）→ 不触发换区（$ 锚定，设计行为——inject 走 03-04）
- 附带说明文字的 `/zone maint 说明`（非纯命令）→ 不触发（§4 正则是 `^/zone\s+<zone>$` 纯形态）——**这是设计精度而非缺陷**：避免误吞自然语句
- unzoned SessionStart → 零输出（stdout 0 字节）
- subagent/resume → 不登记（L-1/startup-only）

## 执行期修复

1. `_ZONE_PROMPT_RE` 曾用 `\s*$` 会吞 `/zone inject ho-123` 参数 → 代理自查修复为 `$` 精确锚定
2. `_zap-title` 缺 transcript_path 崩溃 → 日戳 fallback（设计行为 M-3）

## 结论

**Phase 2 (M1) 通过。** 区身份两条路（主路径注入+补救换区）全部真会话实证。M2 的提示行（pending 探测）按计划留给 03-04。
