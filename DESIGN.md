# zoning — 总设计文档（唯一权威）

> 项目：zoning — Claude Code 功能分区插件
> 版本：1.2（2026-09-08；v1.1 = round-06 审查 16 项修复；v1.2 = V-1~V-9 实验结论回写：8/9 闭环，V-2 留手工验证，详见 discussions/V验证实验报告.md）
> 本文档是全部设计决策的唯一权威。`discussions/round-01~06` 为过程档案，与本文冲突时以本文为准。
> 拍板编号索引（D=方向，P=机制，Q=语法边界，R=契约，A/B=审查裁决）保留在各节，供溯源。

---

## 1. 理念

**不同性质的任务不应共享同一个上下文。** 情况好时影响不大，情况坏时污染上下文、导致结果偏移。

Claude Code 的会话按项目目录组织（`/resume`），没有任务性质维度。zoning 的主张：

1. **区（zone）是会话画像，不是标签。** 进入一个区的会话获得一整套行为边界：身份（zone prompt）、护栏（guards）、交接（handoff 模板）、可见性（命名前缀）。
2. **区之间的联系靠产物交接，不靠意图预测。** 会话结束时产出结构化 handoff 文档，新会话经**人确认**后注入。模型可建议，永不代办。
3. **状态全部可见即文件。** 无 SQLite、无 daemon、无后台进程。`ls` 就是诊断，重放就是重建。
4. **脚本只是哑管道，智能都在模型侧。** `zone` 脚本永远不知道"该不该 handoff"，它只知道有谁、在哪、什么状态。
5. **护栏是威慑级，不是沙箱。** Bash 锁不死（`echo x > file` 即可绕过文件锁），PreToolUse 只能拦已知危险形态。目标是防误操作（讨论时手滑改文件、维护时手滑 force-push），不是防恶意。

**边界与负空间（明确不做）**：LLM 意图预判/自动跳转（D-002）；对话全文索引/自动注入（claude-mem 教训）；收尾性 git 提醒（D-003）；TUI/GUI 外壳；SDK `tag_session`（CLI 不显示）；修改原生 `/resume` UI（无扩展点，能力以官方文档 v2.1.263 核实）。与既有工具的关系（D-004/D-005）：不基于 session-finder 演进（独立新作，设计理念不同）；与 GSD 插件完全独立（目标、理念、架构均不同，不整合）。

## 2. 四区（D-001，封闭集合 P-6）

| 区 | prefix | 定位 | mode_hint | model_hint |
|---|---|---|---|---|
| chore 杂活区 | `--chore` | 简单、朴素、一条线、明确的杂活 | default | haiku（建议） |
| core 核心区 | `--core` | 复杂、非线性、可能引出更多问题的任务 | plan | opus（建议） |
| discuss 讨论区 | `--discuss` | 构建前的需求/架构讨论、方案细化 | default | default（建议） |
| maint 版本维护区 | `--maint` | 维护性 git（分支大扫除、gitignore、远程、tag） | default | default（建议） |

- model 档位无插件强制接口，降级为 prompt 建议 + cz() 糖（P-5）。
- **封闭集合**：不可增删分区（P-6）。架构上声明式 zone 定义天然支持扩展，但"此刻"明说不开自定义。repo 覆盖层出现第五区名 → 警告（非静默）。
- **维护性 vs 收尾性 git（D-003）**：commit/push/PR 等收尾动作留在工作会话内完成，zoning 不提醒、不代办；分支清理/merge/gitignore/远程配置/tag 才是 maint 区的事。

### 2.1 四区 prompt 定稿（M1 基准）

```markdown
# chore
你处于杂活区。这里的任务小而明确：读文档做小修改、修局部 bug、数据备份等。
一次只干一件事，不做范围外的事。
当你发现任务超出"简单、一条线、明确"的边界——需要架构决策、影响多个模块、
或出现了新的开放问题——立即停下来，不要扩大战场。用 /handoff 把现场交给
核心区或讨论区，在那里继续。

# core
你处于核心区。这里的任务复杂、非线性：完整构建项目、重构架构、改数据库
表关系等。
先计划后动手（建议 plan mode 起步）。改动前重读本区约束。执行中遇到需要
重新讨论的规格问题，用 /handoff 回讨论区，不要在执行中自行变更范围。
完成后可用 /handoff 将分支现场交给版本维护区。

# discuss
你处于讨论区。这里的任务是讨论与细化：项目需求、架构、实现效果、修正方案。
本区禁止修改源码（另有护栏强制）。讨论的终点是写 handoff，不是改文件：
讨论收敛后用 /handoff 将决策、开放问题、范围边界交给核心区实施。

# maint
你处于版本维护区。这里只做维护性 git 操作：分支整理、merge、gitignore、
远程配置、tag 等。
不改代码。高危命令另有护栏。改代码的工作属于核心区。
```

## 3. 进入机制：三入口（round-02 方案 C）

| 入口 | 形式 | 分区归属来源 |
|---|---|---|
| **主路径** | `cz core 任务名` → `claude -n "--core 任务名"` | 标题前缀 |
| **补救路径** | 会话内 `/zone core` | UserPromptSubmit hook（A-1/A-2 裁决） |
| **巡视路径** | `/zones` | —（只读） |

**命名语法（Q 系列，含用户反馈修正）**：

- 标题以 `--<zone> ` 开头即视为该分区，zone 名必须恰为四区之一（双重判据，误判面小）。
- 不用 `[core]` 方括号形式：`[]` 是 shell glob 字符类，zsh 下 `[core]` 无匹配文件时直接报 `no matches found`——是硬伤，不只是难看。检测到残留 `[core]` 类前缀时归一化为 `--core`（`zone title` 内 normalize）。
- 手动路径 `claude -n "--core 任务名"` 仍需引号（`-n` 后多词值的现实），仅在无糖场景出现。
- **按名 resume 必须用等号形式（V-3 实测修正）**：`claude --resume "--core 任务名"` 会被 commander 解析为未知 flag 直接报错；正确形式是 `claude --resume="--core 任务名"`。`zone list` / `/zones` 一切给用户的复制命令必须输出等号形式。

**cz() 糖（Q-1，README 提供，不进插件本体）**：

```bash
# ~/.zshrc
cz() {
  local m
  case "$1" in
    chore)   m=haiku ;;           # zone→model 映射（M-6，P-5 档位建议的糖内落实）
    core)    m=opus ;;
    *)       m="" ;;
  esac
  if [[ -n "$m" ]]; then
    claude --model "$m" -n "--$1 ${@:2}"
  else
    claude -n "--$1 ${@:2}"
  fi
}
cz core 重构后端        # 零引号零括号；= claude --model opus -n "--core 重构后端"
```

糖名取 `cz` 不取 `cc`：`cc` 是 `/usr/bin/cc`（clang），遮蔽它是埋暗雷。模型映射不想用 → 删 case 两行即退回裸转发。"建议档位"的否决权在使用者手里，与 P-5 的降级哲学一致。

（无糖场景的手动路径 `claude -n "--core 任务名"` 不带 `--model`：插件不强制档位，档位是糖的一部分。）

**主路径启动时序**：

```
cz core 任务名  →  claude -n "--core 任务名"
  └ SessionStart (source=startup)
      ├ 解析 session 标题前缀 --core → zone=core（无前缀 → unzoned，等补救）
      ├ sidecar 登记索引事件（§7）
      ├ 探测 handoffs/core/ 未消费 handoff
      └ stdout 提示行（如有）：
        "核心区已就绪。未消费 handoff：1) 订单重构决策 → /zone inject ho-xxx"
      （zone prompt 经 hookSpecificOutput.additionalContext 注入）
  └ 首条 prompt（用户输入，或 /zone inject ho-xxx）
```

- **提示≠注入**：SessionStart 只提示待消费 handoff 的存在，永不自动注入（D-002）。
- unzoned 会话 = 静默纯 CC：插件不做任何打扰（无提示、无 zone prompt、无护栏），尊重"没选区的人不受管"。
- 深链（方一案的顺滑保留，handoff 写完时输出，H-2 修正确版）：`claude-cli://open?q=/zone core&cwd=<项目绝对路径>`——打开新终端、prompt 预填 `/zone core` 不发送。人按发送键 → 严格命中补救 hook（换区落 core）→ hook 的 pending 探测（M-3）随即在 additionalContext 提示未消费 handoff → 模型依提示运行 `zone inject <id>` 开工。人按一次发送键，机制不代办（D-002 一致）；深链协议无 name 参数（会话无前缀），落区的任务正是补救路径的职责——组合才是闭环。

## 4. 补救路径：/zone 的双机制裁决（A-2)

| 层 | 职责 |
|---|---|
| **hook**（UserPromptSubmit，匹配 `^/zone\s+(chore|core|discuss|maint)$`） | 写 sessionTitle（补前缀）→ 追加索引事件（source: "command"）→ additionalContext 注入目标区 zone prompt → **pending 探测提示**（M-3：与 SessionStart 同口径，换区后同样看得到"未消费 handoff：… → /zone inject ho-xxx"） |
| **skill**（`/zone` 命令文件） | 占位正文一行："本命令已由 hook 处理，无需操作。"**V-5 实测升级：功能必需，非仅观感**——不存在的命令在扩展期被拒（Unknown command），根本不触发 UserPromptSubmit；补救 hook 的触发依赖本文件存在 |

- 不 block 用户输入：prompt 照常到达模型，模型看到占位正文即无事可做。不依赖"UserPromptSubmit 能否 block"这一未验证行为（V-9 顺带验证，若支持可选升级为拦截式）。
- `/zone inject <id>`（消费 handoff）不是本路径：inject 是 skill 正文引导模型调用 `zone inject`（§5）。
- 换区语义：追加新索引事件（同 sessionId 后事件覆盖前事件），不修改历史。
- **补前缀时 `--<zone> ` 后的名称来源（M-3）**：transcript 首条用户消息截断（~40 字，去换行）；取不到（空会话/解析失败）→ `--core` + 日期（`--core 09-07`）。hook 经 `zone title` 归一化后写入。
- **hook 与 bin 的实现关系（M-5）**：hook 是薄封装，前缀解析/修订 title/索引追加一律调用 `zone` bin 的内部子命令（`_` 前缀、不文档化：如 `zone _register-session`、`zone _zap-title`），自身不实现业务逻辑——**同一逻辑单一实现**，防止 hook 与 bin 漂移。公开命令面不变（A-1 仍成立：无公开 `zone set`）。

## 5. `zone` bin 契约（R-1：命令名 zone；R-2/R-5；A-5）

纯 Python 标准库，随插件 `bin/` 分发（文档确认插件 bin 在会话内 PATH 可见）。参数走 POSIX 风格。

| 子命令 | 语义 | stdout | mutating |
|---|---|---|---|
| `zone which [--session <id>] [--cwd <path>]` | 查会话所属区（**人类诊断命令**，A-5） | `core` 或 `unzoned` | 否 |
| `zone list [--zone=Z]` | 列 handoff 与会话索引摘要 | 表格：id、状态、标题、from→to、相对时间 | 否 |
| `zone pending [--zone=Z]` | 仅未消费 handoff = 目录扫描（存在性）∩ 索引状态（生命周期），见 §7.4 | 同上 | 否 |
| `zone register <file>` | 校验 frontmatter 合法 → 索引登记 pending（**无移动语义**，M-1：文档已按 §6.2 直接写在最终路径） | `registered <id>` | **是** |
| `zone snapshot` | 生成 core→maint 收尾链的现场块（git 分支拓扑 + log 摘要，**纯机器产物**，M-2） | markdown 块 | 否 |
| `zone inject <id> [--force]` | 打印 handoff 全文 + 标记 consumed | 文档全文 | **是** |
| `zone gc [--stale-days=14]` | stale 文档移入 `handoffs/.trash/` | `moved N, kept M` | 是（仅移动） |
| `zone doctor` | 校验 zone 定义合法性 | 问题清单或 `OK` | 否 |
| `zone show <zone>` | 某区定义的最终合并视图 | 合并后 yaml | 否 |
| `zone title <title>` | 归一化 + 前缀判定 | `zone: core, rest: 任务名` 或 `unzoned` | 否 |

- 所有子命令支持 `--json`（附录 A）。
- 退出码：`0` 成功；`2` 用法错误；`3` 找不到匹配的 handoff；`4` 定义非法。
- **R-5**：`inject` 遇已 consumed 文档默认拒绝，`--force` 逃生门（场景：`/clear` 后回看、新会话重读决策）。status 不回退，追加 `re_consumed` 事件。
- **R-2**：`/handoff` 命令正文指示模型**直接写最终路径** `~/.claude/zoning/<project>/handoffs/<to>/<id>.md`（M-1；Write 护栏经 allow_paths 放行）再调用 `zone register <file>`。register 校验 frontmatter（id/from/to/created 存在且合法）才入册——**写入=登记**原子成立。校验失败时提示模型修复 frontmatter，闭环留在模型侧（唯一模型行为可靠性风险点，已知并接受）。
- **M-2**：core→maint 链路的 /handoff 指令指示模型先运行 `zone snapshot`，将其输出**原样嵌入** Snapshot 段——不经 LLM 改写，与 Move 6.3"纯机器产物"承诺一致。
- `zone reindex`：内部逻辑（从 handoffs/ 目录与索引重放重建），不暴露为 CLI 子命令——保底修复手段。

## 6. handoff：产出、模板与生命周期

### 6.1 触发

```
/handoff                      → 交互选目的地 zone（AskUserQuestion，交互会话可用，见 §10 最后一公里）
/handoff discuss              → 直接指定目的地
/handoff discuss "重新讨论状态管理"   → 带附注
```

命令展开为写作指令 + 按链路选择的模板，**模型在上下文完整时主动写出**——这是与"事后压缩全文"（claude-mem 模式）的根本区别。unzoned 会话内 `/handoff` 允许（L-3），frontmatter 记 `from: unzoned`——文档是上下文包，来源不设限。

### 6.2 文档 schema v1（A-3 修订：frontmatter 无 status 字段）

```markdown
---
id: ho-<yyyymmdd>-<4位随机码>
from: discuss
to: core
created: <ISO8601>
tags: []                         # 预留，v1 不消费
---

# <一句话标题>

## Intent           交接意图（一句话 + 触发场景）
## Decisions        已定决策（编号列表）
## Open Questions   开放问题（编号列表）
## Snapshot         现场（分支 / dirty 文件 / 涉及文件清单）
## Why Escalated    为什么超纲（仅 chore→core/discuss 升级链路，其余省略）
## Next Steps       建议的第一步
```

- **frontmatter 是机器层；`# 标题` 起是人机共享层**。inject 打印全文，模型无需解析 frontmatter 也能照 Next Steps 行动。
- **文档写后不可变（A-3）**：机器不回写任何字段；status 只活在索引事件流。人手改文档是人的事。
- ID 形如 `ho-20260907-a1b2`，日常口述友好。

### 6.3 链路模板矩阵

| 链路 | 侧重字段 |
|---|---|
| discuss → core | Decisions + Open Questions + 范围边界 |
| chore → core / discuss（升级） | **Why Escalated** + Snapshot（改到哪了） |
| core → discuss（暴雷回炉） | Blocked By + 具体问题清单 |
| core → maint（收尾） | Snapshot 由纯机器生成（git 分支拓扑 + log 摘要，不经 LLM） |

杂活↔杂活、任何区进入前注入对话全文：明确不做（负空间）。

### 6.4 生命周期（P-4，B-3）

```
pending ──inject──▶ consumed        # 索引事件流状态
pending ──14天未消费──▶ (stale)     # 渲染时派生显示，非存储状态
consumed ──inject --force──▶ re_consumed（status 不回退，追加事件）
任何状态 ──gc──▶ handoffs/.trash/   # 物理移动，不删除
```

- stale 以 `created` 起算（B-3），渲染时派生、gc 时才物化移动，不新增 stale 事件。
- 手工清空 trash 是人的事。**宁可堆积，不可误删**——交接文档是思考痕迹。

### 6.5 消费语义

- 目标区 SessionStart 启动时探测（§3 时序），提示行只列 id/标题/来源区。
- `zone inject <id>` 打印全文；调用既消费（pending→consumed）。**跨区消费允许（B-1）**：handoff 只是上下文包，注入不限于收件区，索引如实记 by。
- 消费幂等性：同一会话重复 inject 同一文档 → 第二次提示已消费，建议 `--force`；不同文档自由。

## 7. 存储与索引（P-1 分治，A-4 布局，B-5 版本）

### 7.1 目录布局

```
repo:  .claude/zones/{chore,core,discuss,maint}.yaml   # zone 定义覆盖层（P-4 封闭）
本地:  ~/.claude/zoning/<project-slug>/                # slug 规则同 ~/.claude/projects（cwd 非字母数字→-）
         index.jsonl                                   # append-only 事件流
         handoffs/<to-zone>/<id>.md                    # 按 to 分目录（收件箱视角）
         handoffs/.trash/                              # gc 产物
```

- 按 to 分目录的收益：`zone pending --zone=core` = 扫一个目录，不扫全索引。
- handoff 属个人痕迹（如 shell history），不进 repo；zone 定义属配置（如 .editorconfig），进 repo 可团队共享。
- 跨机器同步不做（用户自己的云盘/rsync 的事，第一版无云）。

### 7.2 index.jsonl 事件 schema（append-only）

```jsonc
// 每行一个事件；同 key 最后一条事件即现值（事件溯源最小实现，不重写历史）
{"v":1, "ts":"2026-09-07T17:20:00+08:00", "type":"session", "sessionId":"<uuid>", "zone":"core", "title":"--core 重构后端", "cwd":"<abs>", "source":"prefix"}
{"v":1, "ts":"...", "type":"handoff", "id":"ho-20260907-a1b2", "from":"discuss", "to":"core", "status":"pending", "title":"订单重构决策"}
{"v":1, "ts":"...", "type":"handoff", "id":"ho-20260907-a1b2", "status":"consumed", "by":"<sessionId>", "subtype":"inject"}
{"v":1, "ts":"...", "type":"handoff", "id":"ho-20260907-a1b2", "status":"re_consumed", "by":"<sessionId>", "subtype":"inject --force"}
```

- `source`: `prefix`（cz/`-n` 起）| `command`（/zone 补救）——分区归属的可审计来源。
- `by` 记 sessionId 不记人（R-4，机器层事实）。
- `v: 1` 版本字段（B-5），未来迁移空间。
- 体积预估：每事件 ~200B，千会话×十事件 ≈ 2MB。**清单查询直扫 jsonl**（KB~MB 级），不遍历会话目录。jsonl+重放优于 SQLite（R-3：可审计性 > 查询性能，会话上千再议，YAGNI）。
- **并发写（L-2）**：单事件 <512B 单行 append，POSIX 下原子性可接受；`zone doctor` 容忍（跳过并报告）损坏行——多终端并发登记是正常场景，不引入锁。
- 索引诊断/修复：`zone reindex` 内部重放逻辑（保底）。

### 7.4 目录与索引的一致性规则（H-3）

**pending 的真值 = 目录扫描（文件存在）∩ 索引状态（非 consumed/stale）。** 两个来源各司其职：目录答"文件在不在"，索引答"生命周期到哪了"。

| 情形 | 判定 | 处置 |
|---|---|---|
| 有文件、无索引登记（**孤儿**：模型写了文档但 register 失败/漏调） | 视为 pending | stale 判定回退 frontmatter.created；doctor 报告提醒 re-register |
| 有登记、无文件（**幽灵**：人手删/移动了文档） | 视为不存在 | doctor 报告；inject 遇到 exit 3 |
| frontmatter.to ≠ 所在目录名 | 命名错误 | doctor 报告（不影响读取，metadata 以 frontmatter 为准） |

`zone pending` 的输出行来自目录扫描，每行的状态列查索引回填；孤儿行如实标 `(unregistered)`——**不做自动登记**（补登记是 doctor 报告后人的动作，机器不猜状态）。

### 7.3 会话归属查询

- 模型侧：知区全靠 hook 注入的 zone prompt 上下文（A-5），不调 zone which。
- 诊断侧：`zone which --session <id>`；若 V-8 验证 Bash 环境暴露 `CLAUDE_SESSION_ID`，则可免参自动定位（锦上添花，主线不依赖）。
- **PreToolUse 判区依据 = 索引 by sessionId**，不从 cwd 推断——同 repo 多终端可并行不同区（worktree 场景），源真相在索引。

## 8. zone.yaml 规格（覆盖式合并，Q-4；B-4/B-6 裁决；H-1 修：四区 guard 值定稿）

```yaml
# 插件内置默认（repo 覆盖层同 schema，仅可覆盖已列出字段）；此处以 core 为例
name: core
display: 核心
prefix: "--core"
prompt: |            # §2.1 定稿正文
mode_hint: plan       # 仅建议（P-5）
model_hint: opus      # 仅建议（P-5）
inject_on_entry:
  zone_prompt: true
  pending_handoff_scan: true
guards:
  deny_write_edit: false       # 见下表
  bash_block_patterns: []      # maint 拉黑高危 git 模式
  allow_paths: []              # Write/Edit carve-out 白名单，见下表
handoff_out: discuss_to_core   # 引用模板名（链路矩阵 §6.3）
```

**四区 guards 值定稿（H-1；缺省即此表）**：

| zone | deny_write_edit | allow_paths | bash_block_patterns |
|---|---|---|---|
| chore | false | — | — |
| core | false | — | — |
| discuss | **true** | `["**/handoffs/**"]`（B-4：不含 repo 内 `.claude/zones/*.yaml`） | — |
| maint | **true** | `["**/handoffs/**", "`.gitignore`", `"**/.claude/zones/**"`]`（D-001 的 gitignore/远程配置职责 + B-4"想改定义去维护语境"） | 见 §8.2 默认黑名单 |

- **合并方向：repo 覆盖插件默认**，字段级 merge，hook 启动时读入合并，运行期不热重载（会话生命周期内稳定，重启生效）。
- repo 覆盖层：只可覆盖字段值，不可增删分区（P-6）；未知字段 → `zone doctor` 报错、`zone show` exit 4（B-6），不静默降级。
- **B-4**：discuss 区 `allow_paths` 只留 `**/handoffs/**`，不放行 repo 内 `.claude/zones/*.yaml`（讨论区不碰 zone 定义）。

### 8.2 maint 区高危命令默认黑名单（L-6）

```yaml
bash_block_patterns:   # 拦已知危险形态，不枚举全部安全命令（无法穷举且误伤）
  - "git\s+push\s+.*--force(?!\S)"  # 含 --force-with-lease? 否，--force-with-lease 是保护性操作，放行；v1.1 git\s+ 前缀统一
  - "git\s+reset\s+--hard"
  - "git\s+branch\s+(-D|--delete --force)\b"
  - "git\s+clean\s+.*-[a-zA-Z]*f"   # v1.1：字母组合旗标含 f 即拦（-Xfd/-fx 等），-n 干跑不受误伤
  - "git\s+checkout\s+\S+\s+--\s"   # 路径级丢弃
  - "git\s+reflog\s+expire"
  - "git\s+gc\s+--prune=now"
```

匹配对象是 Bash tool 调用的 command 字符串，正则命中 → PreToolUse deny 且提示"维护区护栏：高危 git 操作需人工确认，请改用安全形态或换区执行"。

### 8.1 插件仓库脚手架（B-7 定稿）

```
zoning/
  .claude-plugin/plugin.json
  hooks/hooks.json          # SessionStart / UserPromptSubmit / PreToolUse×2 / SessionEnd
  bin/zone                 # 唯一可执行（纯 Python 标准库）
  skills/
    zone/SKILL.md          # 占位（A-2）
    handoff/SKILL.md       # 写作指令+模板
    zones/SKILL.md         # 巡视，引导调 zone list
  zones/{chore,core,discuss,maint}.yaml   # 内置默认（用户 repo 可放覆盖层）
  README.md                # 理念、cz() 糖、威慑非沙箱声明
```

## 9. hooks 清单（A-1/A-2 裁决后；L-1/M-5 补）

| hook | matcher | 做什么 | 不做什么 |
|---|---|---|---|
| SessionStart | startup 等 | 前缀解析 → 索引登记 → pending 探测 → stdout 提示；zone prompt 经 additionalContext 注入。**main-agent 检查（L-1）**：stdin 的 agent_type 存在且非主会话（subagent/skill 上下文）→ 直接退出，不登记 | 不自动注入 handoff 全文；不改 title（保留用户命名权） |
| UserPromptSubmit | all | 匹配 `^/zone\s+(chore|core|discuss|maint)$` → 写 sessionTitle + 索引事件 + 注入 zone prompt + pending 提示（M-3） | 不侦察普通消息；不 block（V-9 或许可升级） |
| PreToolUse | Write/Edit | 该区 deny_write_edit=true 时 deny，allow_paths 命中放行 | — |
| PreToolUse | Bash | 该区 bash_block_patterns 命中时 deny | — |
| SessionEnd | — | 轻量更新 lastSeen（append 事件） | 不做 LLM 分类（1.5s/60s 限制，且违 D-002 精神） |

- 判区一律索引 by sessionId；未登记（unzoned）→ 全放行（§3：静默纯 CC）。
- PreToolUse 判区失败（索引无此 session）→ 视为 unzoned 放行——护栏只对已选区的会话生效，degrade-to-open。
- **hook 是薄封装（M-5）**：所有业务逻辑（解析/登记/探测/判区）一律调 `zone` bin 内部子命令（`_` 前缀），hook 脚本不含逻辑——同一逻辑单一实现，防漂移。

## 10. /命令清单（含 M-4 最后一公里）

| 命令 | 干什么 | 与 zone bin 关系 |
|---|---|---|
| `/zone` | 无参=交互选区（L 见下）；`/zone <zone>`=hook 已处理（占位证实）；`/zone inject <id>`=skill 引导调 `zone inject` | hook 处理换区（A-2）；inject 走 bin |
| `/handoff` | 按当前区×目标区选模板（§6.3 矩阵），模型写作，写完自动 `zone register`（R-2） | register 走 bin |
| `/zones` | 巡视总览（按区分组：最近会话+未消费 handoff） | 渲染 `zone list` |

`/handoff` 命令正文不写死链路；模型从 hook 注入的 zone prompt 知当前区，从用户参数知目标区。

**`/zone` 无参的最后一公里（M-4）**：AskUserQuestion 选出 `core` 后，模型侧无法自己落区（A-1 否了 `zone set`；Bash 环境拿不到 sessionId，V-8 未定）。流程定为：选择器结果 → 模型回复"已选 core。请发送 `/zone core` 落区" → 用户回车发送 → hook 完成落区。**这一个回车是保留给人的确认动作，不是模型代办**（D-002 的自然延伸：model 可建议，永不代办）。

## 11. 验证清单（写代码前逐项实验；假设若倒，对应设计回炉）

| # | 假设 | 若倒的退路 |
|---|---|---|
| V-1 | ✅已验通过：`session_title: "--core x"` 在 SessionStart stdin（source=startup）| 无需退路 |
| V-2 | ⏳ 唯一手工项：人在 picker 输 `--core` 确认过滤（非交互无法驱动 UI） | 若异常改前缀形 |
| V-3 | ✅已验：按名命中成立，但 `--` 开头标题必须等号形式 `--resume="--core x"`（space 分离形式被当 flag 报错）| /zones 输出全部用等号形式 |
| V-4 | ✅已验通过（实锤取证）：新 Terminal 窗口 `--prefill-b64=L3pvbmUgY29yZQ`（=/zone core）、`--deep-link-cwd-b64` 正确、预填不发送；终端等效 `claude --prefill "/zone core"` | 无需退路 |
| V-5 | ✅已验通过：命令文件存在时 `/zone` 原文进 UserPromptSubmit（stdin 含 session_title/transcript_path/cwd）；且 sessionTitle 写入能力文档确认。**反向发现：不存在的命令不触发 hook → /zone skill 文件为功能必需** | 无需退路 |
| V-6 | ✅已验：12k 字符完整注入无截断（2.1.263 实测，存 2KB 预览+溢出文件机制但正文全量） | zone prompt 余量极大 |
| V-7 | ✅已验不继承（session_title: None），按退路处理：fork 后 /zone 补救 | 已是设计默认 |
| V-8 | ✅已验存在（`CLAUDE_CODE_SESSION_ID`，另有 ENTRYPOINT/PID/EFFORT） | zone which 可免参自动 |
| V-9 | ✅已验：exit 2 与 JSON decision block 均未拦截（本环境实测），A-2"不 block"默认形态即最终形态 | 设计不变 |

## 12. 里程碑（Q-3：M2=v0.1）

垂直切片，每片端到端可验收（理由：横切先框架后填肉会长时间无可感知行为，四区底座自然沉淀，无须预先框架化）。

| 里程碑 | 内容 | 验收 |
|---|---|---|
| M0 底座 | SessionStart hook + zone bin 骨架 + sidecar 索引 | `claude -n "--core x"` 起会话见提示行；`zone list` 出表 |
| M1 注入 | 四区 zone prompt 定稿注入 | `/context` 可见；chore 会话拒斥顺手规划 |
| **M2 旗舰** | discuss→core handoff 全链路 | 交→注→consumed 走通 = **v0.1** |
| M3 护栏 | discuss 锁 Write/Edit、maint 拦高危 git、core 联动 plan 建议 | 三区护栏各自被触发并拦截 |
| M4 其余链路 | 升级链（Why Escalated）+ 收尾链（机器 Snapshot） | 两链路走通 |
| M5 巡视与糖 | /zones + cz() 文档 + README | 按区分组展示 = v1.0 |

## 13. 附录 A：`--json` 输出契约

所有子命令加 `--json` 时输出单行 JSON 对象，`v` 等于索引版本（1）。通用保障字段：

```jsonc
{"ok": true, "v": 1, "cmd": "<子命令>", "data": {…}}       // 成功
{"ok": false, "v": 1, "cmd": "<子命令>", "error": "", "exit": 3}  // 失败，exit 即退出码语义
```

`data` 按子命令：

| cmd | data |
|---|---|
| which | `{zone, title, source}` |
| list / pending | `{items: [{id, from, to, status, title, created, stale, unregistered}]}` |
| register | `{id, path}` |
| inject | `{id, from, to, status, body}` |
| snapshot | `{body}`（markdown 块） |
| gc | `{moved, kept}` |
| doctor | `{problems: [{file, field, message}]}` 或空数组（含 §7.4 孤儿/幽灵/命名错位三类检查） |
| show | `{zone_yaml}`（合并后全文） |
| title | `{zone, rest, normalized}` |

## 14. 决策索引（溯源表）

| 编号 | 内容 | 定义节 |
|---|---|---|
| D-001~006 | 四区 / 产物交接不预测 / 维护性 git / 独立新作 / 与 GSD 独立 / 项目级 | §1 §2 |
| P-1~P-6 | 存储分治 / bin 脚本 / carve-out+威慑声明 / 三态+gc / model 降级 / 封闭集合 | §7 §5 §9 §6.4 §2 |
| Q-1~Q-4 | cz / zoning / M2=v0.1 / 覆盖式定义+doctor | §3 §5 §12 §8 |
| R-1~R-6 | zone / 自动 register / jsonl 重放 / by=sessionId / --force / 整体骨架 | §5 §7.2 |
| A-1~A-6 | hook 落点 / hook+skill 裁决 / 状态只在索引 / 目录布局 / which 降级 / 附录 A 补全 | §4 §5 §6.2 §7.1 §7.3 §13 |
| B-1~B-7 | 跨区 inject / trash 位置 / stale 派生 / 不放行 zones yaml / v:1 / exit 4 / 脚手架定稿 | §6.5 §7.1 §6.4 §8 §7.2 §8 §8.1 |
| H-1~H-3 | 四区 guard 值表 / 深链 q=/zone core / pending 双源一致性 | §8 §3 §7.4 |
| M-1~M-7 | register 无移动 / zone snapshot / 补救探测+title 来源 / 最后一公里 / hook 薄封装 / cz 模型映射 / V-1 退路+V-5 重述 | §5 §5 §4 §10 §9(M-5) §3 §11 |
| L-1~L-6 | subagent 跳过 / 并发 append / from:unzoned / D-004·005 入负空间 / URL 编码 / maint 黑名单 | §9 §7.2 §6.1 §1 §11 §8.2 |
