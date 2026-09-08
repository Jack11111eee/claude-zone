# Milestones

## v1.0 zoning 全量交付 (Shipped: 2026-09-08)

**Phases completed:** 6 phases, 15 plans, 27 tasks

**Key accomplishments:**

- 插件脚手架 + zone bin 基础落地，三个 task 全验收通过。
- SessionStart hook 薄封装落地，五向验收（前缀/无前缀/subagent/非startup/旧语法）全过。
- sidecar 索引引擎落地：登记/重放/查询三面全验收（含坏行容忍与双次登记语义）。
- 受限 YAML 解析器 + show 合并 + doctor 校验全落地，PyYAML 值级对照全过。
- 区身份注入双通道落地：主路径 SessionStart 与补救 /zone 全部真会话实证。
- handoff 生命周期引擎落地：register 校验链与 inject 三态全部独立复测通过。
- pending 双源查询落地：孤儿/排除/隔离/全量四视图独立复测通过。
- doctor 一致性三查落地：孤儿/幽灵/坏行独立复测通过（23 项断言 + 主会话复测）。
- M2 旗舰全链路真会话闭环：discuss 写→register→core 提示→inject→consumed（= v0.1）。
- Write/Edit 护栏落地：六象限+glob 豁免矩阵全过（bin 与 hook 双侧）。
- Bash 护栏落地：十用例独立复测全过（GUARD-04 force-with-lease 精确放行）。
- snapshot+gc 落地：真 repo / 非 git / stale 矩阵独立复测通过。
- 链路矩阵审计：03-04 基础上一处补齐（负空间行）。
- /zones 真会话一次验收通过：分组/孤儿标注/等号警告/深链全对。
- README 落地 + cz 语法 zsh -n 通过 + 24 REQ 全覆盖终审。

---

## v1.1 收尾与加固 (Shipped: 2026-09-08)

**Phases completed:** 4 phases, 4 plans

**Key accomplishments:**

- hook 文案单源化：LABELS 硬编码退役，展示文案经 zones/*.yaml display 单源派生（M-5 精神补完）。
- SessionEnd lastSeen 落地：轻量 append 事件（stub → 实装），zone list 相对时间反映会话最近活动。
- Bash 护栏加固：七条正则 git\s+ 前缀统一 + clean 组合旗标收紧（-Xfd 等绕过面关闭），24 断言测试矩阵入库。
- 发布收口：版本语义化 1.1.0、DESIGN §8.2 快照同步、升级核查。

---
