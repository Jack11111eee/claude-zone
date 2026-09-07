# 讨论稿 Round 05 — 收敛前全案审查

- 日期：2026-09-07
- 状态：✅ 已收口（A/B 全部按建议执行）
- 上游：round-04（R-1~R-6 已定）
- 性质：**汇编总设计文档前的收敛审计**——不改已拍板的方向，只补接线与真空

---

## 0. 审查方法

对 D/P/Q/R 四轮共 23 项拍板做两件事：

1. **接线走查**：每个机制问三个问题——数据从哪来（谁调用它）、写到哪去（状态落在哪）、失败时退到哪。
2. **一致走查**：同一事实是否被两处描述、两处是否同值（单一事实源检验）。

以下发现按严重度排序。A 类为结构性洞（不补则实现时会卡住或自相矛盾）；B 类为微细节（一句话可收敛）。

---

## A. 结构性洞（6 项，均附处置建议）

### A-1 `zone set <zone>` 子命令缺失——补救路径没有落点

round-04 §1 的子命令集里，`register`（R-2）只登记 handoff 文档；但三入口之一的**补救路径**（`/zone core` 会话内换区）需要把"会话 X 现在归 core"写进索引——没有任何子命令干这件事。SessionStart 只覆盖前缀起会话；换区事件无人写入。

**处置建议**：换区登记不放在 CLI 子命令，而是放在 **UserPromptSubmit hook 内直接完成**（hook 收到 session_id/cwd，直接 append 索引事件，source: "command"）。`zone set` 不引入——理由见 A-2。

### A-2 `/zone` 的双机制重叠未裁决

round-02 §1 说补救路径"由 UserPromptSubmit hook 实现最稳"；round-04 §5 又把 `/zone` 列为 skill（模型驱动）。两条路都通向同一件事，但能力不同：**只有 hook 能写 sessionTitle**，只有 skill 能引导模型行为。不裁决会出现 hook 和 skill 各干一半、互相指望。

**处置建议**：hook 全包 + skill 占位。

- **hook**（UserPromptSubmit，匹配 `^/zone\s+(chore|core|discuss|maint)$`）：写 sessionTitle（补前缀）→ append 索引事件 → additionalContext 注入 zone prompt。三件事 hook 都有官方能力（已核实）。
- **skill**（`/zone` 命令文件）仅一行正文："本命令已由 hook 处理，无需操作"——作用只是防止 unknown-command 的报错观感，并留 discoverability 文档。
- 不用 hook 拦截（block）用户输入：prompt 照常到达模型，模型看到 skill 占位正文即知无事可做。零风险，不依赖"UserPromptSubmit 能否 block"这一未验证行为（挂入 V-9 顺带验证）。

### A-3 status 双写矛盾：handoff frontmatter 的 consumed 字段 vs 索引事件

round-04 §3 文档 schema 里有 `consumed / consumed_by`（"注入时由 zone inject 回写"），而 §2 索引是 append-only 事件、且规则是"同 id 最后一条事件为准"。同一个事实两处存储、两种更新方式——冲突时谁赢没有答案，且"回写文件"违背 append-only 哲学。

**处置建议**：**状态只活在索引里**。从 schema v1 中删除 `consumed / consumed_by` 字段，handoff 文档写完后不可变（人想手改是人的事，机器不回写）。单一事实源=索引事件流。

### A-4 本地目录缺项目分段，且 handoffs/<zone>/ 的键未指明

round-04 §0 写 `~/.claude/zoning/{index.jsonl, handoffs/<zone>/}`，但 D-006 拍了项目级作用域——**目录布局里没有项目层**，跨项目会互相混入。且 `<zone>` 是指 `from` 还是 `to` 未写明（round-02 时序图暗示是 to，即"收件箱"，但没成文）。

**处置建议**：布局定为

```
~/.claude/zoning/
  <project-slug>/            # 与 ~/.claude/projects 同名规则（cwd 非字母数字替 -）
    index.jsonl
    handoffs/<to-zone>/       # 按 to（收件箱）分目录——"发往 core 的待办"是消费侧视角
      <id>.md
    handoffs/.trash/
```

按 to 分目录的直接收益：`zone pending --zone=core` = 扫一个目录，不用全索引过滤。

### A-5 `zone which` 无法知道"当前会话是谁"

`zone which` 被 model 从 Bash 调用时，脚本不知道自己运行在哪个会话里（session_id 不在 Bash 工具环境里，未验证 CLAUDE_SESSION_ID 环境变量是否存在）。而设计里 /handoff 需要"当前区"，模型其实不需要 zone which——SessionStart 已注入 zone prompt，模型被告知自己在哪个区。

**处置建议**：`zone which` 降级为**人类诊断命令**（终端里跑，配 `--session <id>` / `--cwd` 参数）；模型侧获取当前区一律来自 hook 注入的 zone prompt 上下文。同步新增 V-8：验证 Bash 工具环境是否暴露 CLAUDE_SESSION_ID（若存在则 zone which 可自动，锦上添花）。

### A-6 附录 A（--json schema）被引用但不存在

round-04 §1 写"JSON schema 见附录 A"，附录从未写出。`--json` 是 hook 内部调用和未来扩展的契约面，不能悬空。

**处置建议**：DESIGN.md 汇编时补全（每个子命令的 JSON 输出结构表）。这属于"总设计文档必须包含"清单，单独立项不再讨论。

---

## B. 微细节（一句话拍板，均已附推荐）

| # | 问题 | 推荐 |
|---|---|---|
| B-1 | 跨区消费：在 chore 会话里 inject 一个 to=core 的 handoff，允许吗 | **允许**（文档只是上下文包，注入不限于收件区；索引如实记 by）。威慑非沙箱哲学的一致延伸 |
| B-2 | trash/ 的位置 | `handoffs/.trash/`（随项目分段，A-4） |
| B-3 | stale 判定基准 | 以 `created` 起算（默认 14 天），**渲染时派生显示**、gc 时才物化移动——不新增 stale 事件 |
| B-4 | discuss 区对 repo 内 `.claude/zones/*.yaml` 是否 carve-out | **不**（讨论区不碰 zone 定义；想改定义去维护语境，护栏白名单只留 handoffs） |
| B-5 | 索引事件加版本字段 | 加 `v: 1`（一行成本，换未来迁移空间） |
| B-6 | `zone show` 遇到 repo 覆盖层含未知字段 | 与 doctor 同口径：exit 4（非法定义不静默降级） |
| B-7 | 插件自身仓库脚手架（plugin.json / skills / hooks / bin / zones 布局）| 不再单独讨论，DESIGN.md 中以"仓库结构"一节定稿 |

---

## C. 验证清单增补

- **V-8**：Bash 工具环境变量中是否有 `CLAUDE_SESSION_ID`（决定 zone which 能否自动定位当前会话；无效不影响主线，A-5 已给出不依赖它的设计）
- **V-9**：UserPromptSubmit hook 是否支持 exit 2 block（若支持，/zone 补救路径可选升级为"拦截式"清理 prompt 流；不支持则维持 A-2 的占位方案）

（V-1~V-7 见 round-03 §4。）

---

## D. 审查结论

- 已拍板的方向性决定（D/P/Q/R 四轮）经走查**无相互矛盾**；
- 上述 A-1~A-6 逐项按建议处置、B-1~B-7 逐项按推荐执行后，**全案无已知未决项**；
- 届时输出 DESIGN.md（唯一权威），四轮+本轮讨论稿降级为过程档案：设计冲突时以 DESIGN.md 为准。

**拍板（2026-09-07）：A-1~A-6、B-1~B-7 全部按建议/推荐执行。** 全案无已知未决项，进入 DESIGN.md 汇编。
