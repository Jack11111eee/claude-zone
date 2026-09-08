# Roadmap: zoning

## Overview

从零到 Claude Code 功能分区插件 v1.0：先立底座（SessionStart hook + zone bin + 索引），再注入区身份（四区 prompt），打通旗舰链路（discuss→core handoff = v0.1），立威慑级护栏，补齐剩余链路（升级+收尾），最后巡视与糖收口。垂直切片，每片端到端可验收。

里程碑映射：Phase 1-6 = DESIGN.md §12 的 M0~M5。Phase 3（M2）收尾即打 v0.1 tag；Phase 6（M5）收尾即 v1.0。

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: M0 底座** - SessionStart hook + `zone` bin 骨架 + sidecar 索引（ZONE-01/03, STORE-01） (completed 2026-09-08)
- [x] **Phase 2: M1 注入** - 四区 zone prompt 定稿注入 + /zone 补救路径（PROMPT-01~03） (completed 2026-09-08)
- [ ] **Phase 3: M2 旗舰 handoff 链路** - discuss→core 全链路 + 存储一致性（HANDOFF-01~05, STORE-02/04, ZONE-02）= v0.1
- [ ] **Phase 4: M3 护栏** - discuss 锁 Write/Edit、maint 拦高危 git、判区联动（GUARD-01~04）
- [ ] **Phase 5: M4 其余链路** - 升级链（Why Escalated）+ 收尾链（机器 Snapshot）+ gc（HANDOFF-06/07, STORE-03）
- [ ] **Phase 6: M5 巡视与糖** - /zones 总览 + cz() 糖 + README = v1.0（REVIEW-01~03）

## Phase Details

### Phase 1: M0 底座

**Goal**: 插件骨架可用：`claude -n "--core x"` 起会话见提示行，`zone list` 出表，索引事件落盘
**Depends on**: Nothing (first phase)
**Requirements**: [ZONE-01, ZONE-03, STORE-01]
**Success Criteria** (what must be TRUE):

  1. 插件脚手架就位（.claude-plugin/plugin.json、hooks/hooks.json、bin/zone 可执行）
  2. `claude -n "--core 测试"` 新会话：SessionStart hook 解析前缀，index.jsonl 出现 session 事件（source: prefix），stdout 提示区就绪
  3. 不带前缀的 `claude` 会话：零打扰（无提示、无索引事件）
  4. `zone which/list/title --json` 返回规范 JSON（附录 A 契约）

**Plans**: 3/3 plans executed

Plans:

- [x] 01-01-PLAN.md
- [x] 01-02-PLAN.md
- [x] 01-03-PLAN.md
- [x] 01-01: 插件脚手架 + zone bin 基础（plugin.json、hooks.json、bin/zone argparse 骨架、title 解析）
- [x] 01-02: SessionStart hook（subagent 跳过 L-1、前缀解析、索引登记、stdout 提示）
- [x] 01-03: sidecar 索引（index.jsonl 追加、title/which/list 渲染、--json 契约）

### Phase 2: M1 注入

**Goal**: 四区身份进会话：zone prompt 注入 + /zone 补救换区 + 提示（不注入）未消费 handoff
**Depends on**: Phase 1
**Requirements**: [PROMPT-01, PROMPT-02, PROMPT-03]
**Success Criteria** (what must be TRUE):

  1. 主路径会话启动即见所在区 prompt（/context 可核），文本与 DESIGN §2.1 定稿一致
  2. 会话内 `/zone core`：title 被补写前缀、追加 source:command 事件、模型收到 core zone prompt
  3. /zone 命令文件存在且为占位正文（A-2），hook 的 UserPromptSubmit 被触发
  4. 换区持续有效：同会话先 /zone core 后 /zone discuss，档位随最后事件

**Plans**: 2/2 plans executed

Plans:

- [x] 02-01-PLAN.md
- [x] 02-02-PLAN.md

- [x] 02-01: zones/*.yaml 四区定义 + zone show 合并视图 + doctor 校验
- [x] 02-02: UserPromptSubmit hook（/zone 匹配、title 修订、注入、pending 提示）+ /zone skill 文件

### Phase 3: M2 旗舰 handoff 链路 (= v0.1)

**Goal**: discuss→core 交→注→consumed 全链路走通；存储双源一致性（doctor 三类检查）
**Depends on**: Phase 2
**Requirements**: [HANDOFF-01, HANDOFF-02, HANDOFF-03, HANDOFF-04, HANDOFF-05, STORE-02, STORE-04, ZONE-02]
**Success Criteria** (what must be TRUE):

  1. 讨论区会话 `/handoff core`：模型按模板写出合规文档（frontmatter id/from/to/created）到 handoffs/core/，`zone register` 校验通过（写入=登记）
  2. 新 core 会话启动（或 /zone core 换区）看到"未消费 handoff"提示行
  3. `zone inject ho-xxx` → 打印全文 → 索引 consumed；重复 inject 默认拒绝 exit 语义正确，`--force` 追加 re_consumed
  4. `zone pending` 列表与目录∩索引双源一致：孤儿 (unregistered) 如实标注；幽灵 exit 3
  5. 上游 handoff 链路确认 fake frontmatter 时 register 拒绝且提示模型修复（闭环留模型侧）

**Plans**: 2/4 plans executed

Plans:

- [x] 03-01-PLAN.md
- [x] 03-02-PLAN.md
- [ ] 03-03-PLAN.md
- [ ] 03-04-PLAN.md

- [x] 03-01: handoff schema + register/inject（frontmatter 校验、生命周期事件、--force 语义）
- [ ] 03-02: pending 双源查询（目录扫描∩索引状态、stale 派生、孤儿标注）
- [ ] 03-03: doctor（四区定义校验 + 孤儿/幽灵/命名错位 + 索引损坏行容忍）
- [ ] 03-04: /handoff skill + discuss_to_core 模板 + SessionStart/UPS pending 探测提示行

### Phase 4: M3 护栏

**Goal**: 威慑级护栏生效：discuss 锁 Write/Edit（carve-out handoff 路径）、maint 拦 7 类高危 git、未登记会话放行
**Depends on**: Phase 3
**Requirements**: [GUARD-01, GUARD-02, GUARD-03, GUARD-04]
**Success Criteria** (what must be TRUE):

  1. discuss 会话内 Write/Edit 源码 → PreToolUse deny + 指引提示；写 handoffs/ 路径 → 放行
  2. maint 会话内 `git push --force` → deny + "维护区护栏"提示；`git push --force-with-lease` → 放行
  3. maint 区写 .gitignore、.claude/zones/** → 放行；写源码 → deny
  4. unzoned 会话（无前缀、无 /zone）→ 一切放行（零打扰）
  5. 判区 by sessionId（同 repo 双终端不同区互不串扰）

**Plans**: 2 plans

Plans:

- [ ] 04-01: PreToolUse Write/Edit hook（deny_write_edit + allow_paths glob 匹配）
- [ ] 04-02: PreToolUse Bash hook（bash_block_patterns 正则、判区 by sessionId、maint 黑名单）

### Phase 5: M4 其余链路

**Goal**: 升级链（chore→core/discuss）+ 收尾链（core→maint 机器 Snapshot）+ gc 走通
**Depends on**: Phase 3
**Requirements**: [HANDOFF-06, HANDOFF-07, STORE-03]
**Success Criteria** (what must be TRUE):

  1. chore 会话 `/handoff discuss "理由"`：文档含 Why Escalated 段 + Snapshot（LLM 写）
  2. core 会话 `/handoff maint`：模型先运行 `zone snapshot`，其输出原样嵌入 Snapshot 段（不经 LLM 改写）
  3. `zone gc` 移动 14 天 stale 文档至 .trash/（不删除；moved N, kept M）
  4. 三链路模板选择 = 表名矩阵（§6.3）自动按 from×to 路由

**Plans**: 2 plans

Plans:

- [ ] 05-01: zone snapshot（git 分支拓扑+log 摘要纯机器产物）+ gc
- [ ] 05-02: 链路模板路由（升级链 Why Escalated、收尾链指令）+ /handoff 参数化

### Phase 6: M5 巡视与糖 (= v1.0)

**Goal**: /zones 按区分组总览 + README（理念、cz() 糖、威慑声明）+ 深链格式
**Depends on**: Phase 4, Phase 5
**Requirements**: [REVIEW-01, REVIEW-02, REVIEW-03]
**Success Criteria** (what must be TRUE):

  1. `/zones` 输出按区分组：每区最近会话 + 未消费 handoff；给用户的 resume 命令一律等号形式
  2. README 提供可复制的 cz() zsh 函数（zone→model 映射含 chore→haiku、core→opus）
  3. handoff 写完时的深链输出格式 `claude-cli://open?q=/zone core&cwd=<abs>` 正确（URL 编码）
  4. 全部 24 条 v1 需求验收通过 = v1.0 tag

**Plans**: 2 plans

Plans:

- [ ] 06-01: /zones skill（渲染 zone list、等号形式命令、深链）
- [ ] 06-02: README（理念、cz() 糖、威慑非沙箱声明、装法）

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. M0 底座 | 3/3 | Complete    | 2026-09-08 |
| 2. M1 注入 | 2/2 | Complete    | 2026-09-08 |
| 3. M2 旗舰 handoff | 2/4 | In Progress|  |
| 4. M3 护栏 | 0/2 | Not started | - |
| 5. M4 其余链路 | 0/2 | Not started | - |
| 6. M5 巡视与糖 | 0/2 | Not started | - |
