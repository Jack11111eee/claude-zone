# Roadmap: zoning

## v1.1 收尾与加固（Phases 7-10）

当前里程碑：v1.0 交付后的收尾三件事 + 发布收口——单源收敛（M-5 精神补完）、SessionEnd lastSeen 补全（§9 设计残留）、Bash 护栏加固（§8.2 已知缺口）、版本号语义化。全程不新增用户可见功能面，v1.1 = 更硬的 v1.0。

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 7: 单源收敛** - hook LABELS 硬编码收敛到 zones/*.yaml display 单源（CONSOL-01/02） (completed 2026-09-08)
- [ ] **Phase 8: SessionEnd lastSeen** - 会话结束轻量事件补全，zone list 相对时间活化（SESS-01/02）
- [ ] **Phase 9: Bash 护栏加固** - §8.2 非常规形态补齐 + 测试矩阵固化（GUARD-05/06）
- [ ] **Phase 10: v1.1 发布收口** - 版本语义化 1.0.0→1.1.0、marketplace 升级核查（PACK-01/02）= v1.1 tag

## Phase Details

### Phase 7: 单源收敛

**Goal**: 四处 hook 的 zone 文案（LABELS dict）不再各自维护，从 yaml display 单源派生，行为零回归
**Depends on**: Nothing (first phase of v1.1)
**Requirements**: [CONSOL-01, CONSOL-02]
**Success Criteria** (what must be TRUE):

  1. `session_start.py` / `user_prompt_submit.py` / `pre_tool_use_write.py`（`pre_tool_use_bash.py` 如有）内已无硬编码 LABELS，文案读自 zones/*.yaml（经 bin 或直读）
  2. 真会话回归：`claude -n "--core x" -p` 提示行文案与 v1.0 逐字一致（或仅更一致）；discuss 护栏拒绝理由逐字一致
  3. yaml 改一个 display 字段 → hook 文案随之变化（单源性证明）
  4. 既有 hook 验收测试全过（无回归）

**Plans**: TBD（预计 1-2 plans）

- [x] 07-01-PLAN.md

### Phase 8: SessionEnd lastSeen

**Goal**: 会话结束轻量 append lastSeen 事件（DESIGN §9），zone list 相对时间反映最近活动
**Depends on**: Phase 7
**Requirements**: [SESS-01, SESS-02]
**Success Criteria** (what must be TRUE):

  1. 已登记会话结束 → index.jsonl 多一条 lastSeen 事件，重放后 `zone list` 相对时间以此为最新
  2. unzoned 会话结束 → 零打扰（无事件、无输出）
  3. hook 快：无 LLM 调用、纯一次 append（对齐 §9「轻量」裁决）
  4. 同键 last-event-wins 重放语义不被破坏（lastSeen 与 session 事件共存不冲突）

**Plans**: TBD（预计 1-2 plans）

### Phase 9: Bash 护栏加固

**Goal**: §8.2 七条正则补已知非常规形态（git clean 删除旗标、多空格），测试矩阵固化防回归
**Depends on**: Phase 7
**Requirements**: [GUARD-05, GUARD-06]
**Success Criteria** (what must be TRUE):

  1. `git clean -Xfd` / `git clean -xfd` / `git  clean -Xf`（多空格）等在 maint 区被拒，理由文案照 §8 格式
  2. 回归矩阵：v1.0 十用例全过（含 `--force-with-lease` 放行、chore/core 区不拦 git）
  3. 新形态有独立测试用例并全部通过

**Plans**: TBD（预计 1 plan）

### Phase 10: v1.1 发布收口

**Goal**: 版本号语义化 + marketplace 升级核查 = v1.1 tag
**Depends on**: Phase 7, Phase 8, Phase 9
**Requirements**: [PACK-01, PACK-02]
**Success Criteria** (what must be TRUE):

  1. plugin.json 版本为 1.1.0；README 标注里程碑↔版本对应
  2. 本地 marketplace 拉新版流程走通（升级后行为抽查不变）
  3. MILESTONES.md / CHANGELOG 记录 v1.1 变更四条
  4. 以上全过 → v1.1 tag

**Plans**: TBD（预计 1 plan）

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 8 → 9 → 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 7. 单源收敛 | 1/1 | Complete    | 2026-09-08 |
| 8. SessionEnd | 0/? | Not started | - |
| 9. 护栏加固 | 0/? | Not started | - |
| 10. 发布收口 | 0/? | Not started | - |
