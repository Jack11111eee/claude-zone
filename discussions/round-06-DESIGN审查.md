# 讨论稿 Round 06 — DESIGN.md 权威文档审查

- 日期：2026-09-07
- 状态：✅ 审查完成（16 项发现：高 3 / 中 7 / 低 6；全部已处置，DESIGN.md 升至 v1.1）
- 对象：DESIGN.md v1.0（汇编稿）
- 方法：机制接线走查（每机制问：数据从哪来/写到哪/失败退哪）+ 单一事实源检验 + 四轮拍板遗漏扫描

---

## 高严重度（逻辑矛盾，将卡住主流程）

### H-1 maint 区改不了 .gitignore——与 D-001 直接矛盾 ⚠️ 自相矛盾

D-001 定义 maint 区负责"分支 merge、gitignore、远程配置"；round-02 §3 也明确放行 .gitignore 编辑。但 §8 的 `allow_paths` 只写 `["**/handoffs/**"]`，且 maint 的 `deny_write_edit` 值从未被指定 → 按 §8 原样实现，maint 会话被自己的护栏锁在门外。
**另发现根因**：四区 guard 具体值表整体缺失（§8 只有 core 示例 yaml）。
**修复**：补四区 guard 值表——maint：`deny_write_edit=true`，`allow_paths` 加 `.gitignore` 与 `.claude/zones/**`（B-4 原话"想改定义去维护语境"本就指向 maint 放行 zones 定义）。

### H-2 深链旗舰流程断裂 ⚠️ 组合缺陷

v1.0 的深链 `q=/zone inject <id>` 落地即断：深链打开的新会话**无命名前缀**（深链协议无 name 参数）→ unzoned → 无 core 身份；且组合式首条 prompt 无法命中严格正则 `^/zone\s+core$` → 换区 hook 不触发。"一键到核心区"实际落进一个无区会话。
**修复**：深链 q 固定为 `/zone core`——严格命中补救 hook → 落区 + （配套 H-6 修复后）pending 提示一并发出 → 模型依提示完成 inject 与开工。人按一次发送键，机制不代办（D-002 一致）。handoff id 由 hook 的提示行携带。

### H-3 pending 的双源真相无一致性机制 ⚠️ 决策间隐性冲突

§5 说 pending"扫 `handoffs/<zone>/` 目录"，A-3/§7.2 说"status 只活在索引"——两个来源（目录文件、索引事件）之间的孤儿（有文件无登记：模型写了没 register）与幽灵（有登记无文件：人手删）场景完全没有裁决；`zone doctor` 也不管这个。
**修复**：新增 §7.4 一致性规则——pending = 目录扫描（存在性）∩ 索引状态（生命周期）；doctor 增加三项检查（孤儿/幽灵/frontmatter.to ≠ 所在目录）；孤儿文件 stale 判定回退 frontmatter.created。

## 中严重度（细化失败 / 欠规格）

### M-1 `zone register` 的"移入正式目录"语义悬空

staging 位置从未定义。若模型直写最终路径，register 的"移入"不存在。
**修复**：register = 校验 + 索引登记，**无移动语义**；/handoff 指令指示模型直接写最终路径 `handoffs/<to>/<id>.md`（Write 护栏经 allow_paths 放行）。

### M-2 core→maint 的"纯机器 Snapshot"没有承载者

§6.3 说 Snapshot"纯机器生成、不经 LLM"，但没有任何子命令生成它——模型自己跑 git 再粘贴就不是"纯机器"。
**修复**：新增子命令 `zone snapshot`（分支拓扑 + log 摘要 → markdown 块），/handoff（core→maint）指令指示模型先运行并**原样嵌入**。

### M-3 补救换区 hook 不做 pending 探测；换区的 title 取名来源未定义

SessionStart 的 pending 提示只在启动时出现一次；`/zone core` 之后看不到待办。且 hook 补前缀时 `--core ` 后面跟什么（拿什么当任务名）没写。
**修复**：补救 hook 同样执行 pending 探测并附加提示；title = `--<zone> ` + transcript 首条用户消息截断（~40 字，失败则日期）。

### M-4 /zone 无参交互选区的"最后一公里"未成文

AskUserQuestion 选完区后，模型自己无法落区（A-1 否了 `zone set`；模型侧 Bash 拿不到 sessionId，V-8 未定）。流程必然是"模型提示用户发送 `/zone <所选>`"，但 v1.0 没写——这是 UX 上唯一诚实可行的一步，必须成文。
**修复**：§10 成文：选择器结果 → 模型提示用户发送 `/zone core`（一个回车完成落区，D-002 的自然延伸）。**此处是保留给人的一个回车，不是模型的代办。**

### M-5 hooks 与 bin 的逻辑双实现漂移风险

前缀解析、索引追加若在 hook 脚本和 bin 各写一遍，必然漂移。
**修复**：hook 是薄封装，一律调用 bin；bin 提供内部子命令（`_` 前缀、不文档化）承载登记/探测。公开命令面不变（A-1 仍然成立——没有公开的 `zone set`）。

### M-6 cz() 丢了 P-5 的模型档位映射

P-5 明说"可并入 shell 糖"，v1.0 的 cz() 是裸转发，档位区分只剩 prompt 一行字（最弱的建议形态）。
**修复**：cz() 内置 zone→model 映射（chore→haiku，core→opus；delete 两行即关闭）。**默认带档位是糖场景的合理默认，用户可否决。**

### M-7 V-1 的退路链欠细化；V-5 未瞄准真风险

V-1 若倒（SessionStart 拿不到 title），"UserPromptSubmit 反查"怎么反查（stdin 无 title，须读 transcript，格式未验证）没写。V-5 的真风险点是"斜杠命令输入是否触发 UserPromptSubmit"（官方另有 UserPromptExpansion 事件暗示可能不触发），v1.0 表述没瞄准它。
**修复**：V-1 退路链成文（transcript 提取 → 仍败则补救路径承担登记）；V-5 重述 + 失败退路换 UserPromptExpansion。

## 低严重度（补丁级，一并修复）

| # | 问题 | 修复 |
|---|---|---|
| L-1 | subagent 上下文触发 SessionStart 会污染索引 | §9：agent_type 非主会话直接跳过登记 |
| L-2 | 多终端并发 append index.jsonl 无说明 | §7.2：单事件 <512B，POSIX 行级 append 原子性可接受；doctor 容忍损坏行 |
| L-3 | unzoned 会话 `/handoff` 的 from 未定义 | 允许，from: `unzoned` |
| L-4 | 负空间漏 D-004/D-005（与 session-finder/GSD 独立） | §1 补一句 |
| L-5 | V-4 的 URL 编码细节（空格→%20）在汇编时脱落 | §11 补 |
| L-6 | maint 高危命令默认黑名单未列 | §8.2 给默认正则表 |

---

## 处置汇总

- 16 项全部修复进 DESIGN.md v1.1；
- 其中 **H-2（深链 q=/zone core 方案）**、**M-4（最后一公里=人的一个回车）**、**M-6（cz 默认带模型档位）** 三处存在真实可选项，按推荐已实施、报请用户否决权；
- 未发现需推翻既有拍板（D/P/Q/R/A/B 35 项）的发现——全部是接线级与细化级问题，与五轮方向一致性完好。
