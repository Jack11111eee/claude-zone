# Requirements: zoning

**Defined:** 2026-09-08
**Core Value:** 不同性质的任务不共享同一个上下文（防污染、防结果偏移）

## v1 Requirements

Requirements for initial release (v1.0 = M0~M5). Each maps to roadmap phases. 所有条目以 DESIGN.md v1.2 对应章节为准。

### Zone Foundation（区底座）

- [ ] **ZONE-01**: `claude -n "--core x"` 启动会话，SessionStart hook 解析标题前缀，登记索引事件，未选区（unzoned）会话零打扰
- [ ] **ZONE-02**: 四区 zone 定义以 yaml（插件内置默认 + repo 覆盖层），字段级覆盖合并，未知字段报错不静默
- [ ] **ZONE-03**: `zone` bin（纯 Python 标准库）可执行 which/list/pending/register/snapshot/inject/gc/doctor/show/title 全部公开子命令

### Prompt Injection（区身份）

- [ ] **PROMPT-01**: 启动主路径会话获得对应区 zone prompt（经 SessionStart hookSpecificOutput.additionalContext）
- [ ] **PROMPT-02**: 会话内 `/zone <zone>` 经 UserPromptSubmit hook 换区：写 title、追加索引事件、注入 zone prompt、提示未消费 handoff
- [ ] **PROMPT-03**: /zone 命令文件存在（占位正文），保证 slash 输入触发 UserPromptSubmit（V-5 实测前提）

### Handoff（交接链路）

- [ ] **HANDOFF-01**: /handoff 命令展开为写作指令+按链路模板，模型直接写最终路径，写后调用 `zone register` 登记（写入=登记原子）
- [ ] **HANDOFF-02**: handoff schema v1：frontmatter（id/from/to/created/tags）+ 正文七段模板（Intent/Decisions/Open Questions/Snapshot/Why Escalated/Next Steps）
- [ ] **HANDOFF-03**: `zone inject <id>` 打印全文并标记 consumed；已消费默认拒绝 + `--force` 逃生门（re_consumed 追加事件，status 不回退）
- [ ] **HANDOFF-04**: 目标区启动/换区时提示未消费 handoff 列表（提示≠注入，人确认）
- [ ] **HANDOFF-05**: discuss→core 链路（旗舰，=v0.1）：Decisions+Open Questions+范围边界模板走通
- [ ] **HANDOFF-06**: 升级链（chore→core/discuss，Why Escalated + Snapshot 模板）
- [ ] **HANDOFF-07**: 收尾链（core→maint，Snapshot 由 `zone snapshot` 纯机器生成原样嵌入）

### Guards（护栏）

- [ ] **GUARD-01**: discuss 区 deny_write_edit=true，allow_paths=["**/handoffs/**"] 放行 handoff 写入
- [ ] **GUARD-02**: maint 区 deny_write_edit=true，allow_paths 增 `.gitignore`+`**/.claude/zones/**`；bash_block_patterns 拦 7 类高危 git 形态
- [ ] **GUARD-03**: PreToolUse 判区 by sessionId 索引；未登记会话全放行（degrade-to-open）
- [ ] **GUARD-04**: maint 区欣赏性例外：`--force-with-lease` 不拦（保护性操作）

### Review & Sugar（巡视与糖）

- [ ] **REVIEW-01**: /zones 巡视命令：按区分组（最近会话+未消费 handoff），给用户的复制命令一律等号形式 `--resume="--core x"`
- [ ] **REVIEW-02**: README 含理念、cz() 糖（zone→model 映射）、威慑非沙箱声明
- [ ] **REVIEW-03**: 深链输出 `claude-cli://open?q=/zone core&cwd=...` 格式正确（H-2 修正确版）

### Storage & Consistency（存储一致性）

- [ ] **STORE-01**: 本地 `~/.claude/zoning/<project-slug>/`：index.jsonl append-only 事件流（v:1）+ handoffs/<to>/<id>.md + .trash/
- [ ] **STORE-02**: pending 真值 = 目录扫描 ∩ 索引状态（H-3）：孤儿、幽灵、命名错位三类一致性检查入 doctor
- [ ] **STORE-03**: `zone gc` stale（created 起算 14 天）移入 .trash/（移动不删除）；
- [ ] **STORE-04**: index 损坏行 doctor 容忍跳过并报告（并发 append 场景，L-2）

## v2 Requirements

（无——v1 即完整封闭集合）

## Out of Scope

| Feature | Reason |
|---------|--------|
| LLM 意图预判/自动跳转 | D-002 用户撤回；模型可建议永不代办 |
| 对话全文自动注入 | claude-mem 教训；与 handoff 理念相反 |
| 自定义第五区 | P-6 封闭集合，v1 明确不开 |
| 沙箱级防护 | 威慑级护栏哲学（§1 第 5 条） |
| TUI/GUI/SQLite/daemon/云同步 | 状态全部可见即文件 |
| 修改原生 /resume UI | 无扩展点（官方文档核实） |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ZONE-01 | Phase 1 (M0) | Pending |
| ZONE-02 | Phase 3 (M3) | Pending |
| ZONE-03 | Phase 1 (M0) | Pending |
| PROMPT-01 | Phase 2 (M1) | Pending |
| PROMPT-02 | Phase 2 (M1) | Pending |
| PROMPT-03 | Phase 2 (M1) | Pending |
| HANDOFF-01 | Phase 3 (M2) | Pending |
| HANDOFF-02 | Phase 3 (M2) | Pending |
| HANDOFF-03 | Phase 3 (M2) | Pending |
| HANDOFF-04 | Phase 3 (M2) | Pending |
| HANDOFF-05 | Phase 3 (M2) | Pending |
| HANDOFF-06 | Phase 5 (M4) | Pending |
| HANDOFF-07 | Phase 5 (M4) | Pending |
| GUARD-01 | Phase 4 (M3) | Pending |
| GUARD-02 | Phase 4 (M3) | Pending |
| GUARD-03 | Phase 4 (M3) | Pending |
| GUARD-04 | Phase 4 (M3) | Pending |
| REVIEW-01 | Phase 6 (M5) | Pending |
| REVIEW-02 | Phase 6 (M5) | Pending |
| REVIEW-03 | Phase 6 (M5) | Pending |
| STORE-01 | Phase 1 (M0) | Pending |
| STORE-02 | Phase 3 (M2) | Pending |
| STORE-03 | Phase 5 (M4) | Pending |
| STORE-04 | Phase 3 (M2) | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-08*
*Last updated: 2026-09-08 after project init (auto, DESIGN.md v1.2 mapping)*
