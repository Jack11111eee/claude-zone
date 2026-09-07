# 讨论稿 Round 03 — 命名语法修正与 MVP 切割

- 日期：2026-09-07
- 状态：✅ 已收口（Q-1~Q-4 全拍，见文末）
- 上游：round-02（P-1~P-6 已定）

---

## 1. 命名语法修正（用户反馈直达）

### 问题

round-02 主路径写的是 `claude -n "[core] 任务名"`。用户反馈：引号影响输入，去掉；如果一定要有引导前缀，用 `--`，不要用引号包裹的 `[]`。

除了输入体验，还有一个**硬伤**：`[` `]` 在 zsh（和 bash）里是 glob 字符类。裸敲 `claude -n [core]` 时 shell 会先做文件名展开——当前目录无匹配文件时 zsh 直接报 `no matches found: [core]`，命令根本进不去 claude。也就是说旧语法不只是难看，在默认 shell 里是残废的。（按 `--core` 新语法则无此事：`--` 开头的参数是普通词，无 glob 含义。）

### 新语法

| 层 | 语法 | 说明 |
|---|---|---|
| 日常入口（shell 糖） | `cz core 重构后端` | 零引号、零括号、自由词。见下 |
| 手动路径 | `claude -n "--core 重构后端"` | 仍需引号（`-n` 后多词值在 shell 里的现实），仅在无糖场景/演示文档里出现 |
| 前缀定义域 | `[--chore]` / `[--core]` / `[--discuss]` / `[--maint]` | 标题以 `--<zone> ` 开头即视为该分区 |

**为什么糖不能叫 `cc`**：`cc` 是 `/usr/bin/cc`（clang 的别名）,每个 unix 系统都有它，函数遮蔽会埋暗雷。**建议 `cz`**（zone 首尾,二字键，左手区，无冲突），形如：

```bash
# ~/.zshrc
cz() { claude -n "--$1 ${@:2}"; }
cz core 重构后端        # 完全无引号
cz discuss 新项目需求讨论
```

**兼容与边界**（实现时处理）：

- 带头发起的会话有全局重启后补前缀的课题→ 即 Round-02 已定的 `/zone core` 补救路径，无新增。
- 弯引号残留：检测到 `["[core]"]` 类残留时静默归一化为 `--core`（脚本里 normalize）。
- 非分区会话名以 `--` 开头的误判面：CC 的会话名里 `--` 开头本来就罕见，且分区注册判据=前缀后的 token 恰为四区名之一，双重条件，误判面小。
- `--resume <name>` 命中：文档确认按名可跨 repo 解析（v2.1.223+），picker 里搜索 `--core` 即为该区分过滤——picker 搜索框不会把 `--` 当参数（要实现时验证，V 清单）。

### 更新后的主路径时序（替代 round-02 版）

```
cz core 重构后端
  └ claude -n "--core 重构后端"
      └ SessionStart (source=startup)
          ├ 解析 session 标题前缀 `--core` → zone=core
          ├ sidecar 登记
          ├ 探测未消费 handoff（to=core）
          └ stdout 提示（如有）："核心区已就绪。未消费 handoff：1) discuss ... → /zone inject ho-xxx"
```

对照：round-02 的问题表里方案 B 的缺点"依赖用户记得敲前缀"由糖解决——`cz core x` 与 `claude -n "..."` 手动长写的输入成本几乎一样；而方案 A 的问题（杂聊头部污染）在糖引入后依然回避不了（裸 `claude` 起手就没有分区），这印证了"补救路径"存在的必要性——不改就是未分区（人是目的性动物，想着核心任务的人们第一动作会搜出糖）。

## 2. MVP 切割（垂直切法）

**切法哲学**：每片 MVP 都是端到端可验收的完整体验,而不是横切的层。理由：横切（先做全部 zone 定义框架再填四区）会导致很长时间内没有任何可感知行为，且四区共享的底座正是各启动/护栏/交接实现在切的过程中自然沉淀出来的,不需要预先框架化。

| 里程碑 | 内容 | 验收 |
|---|---|---|
| **M0 底座** | SessionStart hook（前缀解析→zone 及未消费 handoff 探测）+ `zone` bin 脚本骨架（list / inject / gc） + sidecar 索引读写 | scratch repo 里 `claude -n "--core x"` 起会话，SessionStart 输出提示行；`zone list` 出分区列表 |
| **M1 进入链** | zone prompt 注入（议定四区 prompt 内容） | 起会话后 `/context` 或观察行为可验证 prompt 生效；chore 会话对"顺手规划架构"表现拒斥 |
| **M2 旗舰链路：discuss→core handoff** | `/handoff` 命令 + handoff 文档模板 + `/zone inject` | **整个插件的灵魂链路**：讨论→交付→注入→标记 consumed，全链路走通=v0.1 发布线 |
| **M3 护栏** | discuss 锁 Write/Edit（除 handoff 目录）+ maint 拦高危 git + core 联动 plan 建议 | 在 discuss 会话里让模型改源码→被拦；maint 会话 push --force→被拦 |
| **M4 其余链路** | chore→core/discuss 升级链（Why Escalated 字段）＋ core→maint 收尾链（纯机器 Snapshot） | 杂活升级场景走通；收尾链路机器产物正确 |
| **M5 巡视与糖** | `/zones` 总览 + cz() 糖文档 + README | /zones 按区分组展示会话与未消费 handoff |

M2 完成即 v0.1（功能上已解决用户最核心的"讨论→构建"痛点）；M5 完成=v1.0（含全部链路+护栏+巡视）。

## 3. zone 定义的"覆盖式"层级（P-1 的实现细化)

P-1 拍板分区定义进 repo。细化：

```
repo/.claude/zones/core.yaml      ← 团队/项目级（可覆盖字段）
        ↑ 覆盖（按字段 merge）
插件内置 zones/core.yaml（默认）   ← 随插件分发,插件更新时演进
```

- 对封闭四区：插件内置默认即天,repo 级仅可**覆盖字段**（如改某区 prompt 措辞、调 maint 黑名单正则）,**不可增删分区**（P-6）。检测到 repo 级 yaml 出现非四区名 → 启动时警告而非静默忽略。
- 校验放在 `zone` bin 里（`zone doctor`）,不依赖 hook 运行时检查。

**四区 prompt 初稿（M1 敲定）**：

- chore：小而明确。一次只干一件事。发现超出明确范围的问题 → 不扩大战场，当场 `/handoff discus(core)` 升级。
- core：复杂非线性任务区。先计划（plan mode）后动手，改动前重读 zone prompt。
- discuss：本区禁止修改源码（护栏另有强制）。讨论的终点是写 handoff,不是改文件。
- maint：只做维护性 git 操作。改代码不是本区的事;高危命令有护栏。

## 4. 验证清单 V（实验前置，逐项过）

> 这些是设计建立在官方文档上的关键假设，写代码前在 scratch 环境逐一实验确认，假设若倒则设计该处回炉。

- **V-1**：`claude -n "--core x"` 的 `--core` 是否作为 `session_title` 出现在 SessionStart stdin 的 `session_title` 字段？（若是 → 前缀解析可直接用官方字段；若否 → 需在 SessionStart 时以 session_id 反查刚写入的会话名,或改用 UserPromptSubmit 时点解析）
- **V-2**：picker `/` 搜索 `--core` 是否正常过滤？（`--` 不被当 flag）
- **V-3**：`claude --resume "--core x"` 按名命中（v2.1.223+ 文档行为）
- **V-4**：深链 `claude-cli://open?q=/zone inject ho-x&cwd=<abs>` 打开后，首条 prompt 是否如预期为 q 内容？（q 里含空格/斜杠的 URL 编码规格）
- **V-5**：UserPromptSubmit hook 检测 `/zone core` 斜杠命令并写入 `sessionTitle` + `additionalContext` 全链路（round-02 补救路径）——含弯引号 normalize
- **V-6**：SessionStart `additionalContext` 实际注入长度上限的体感（已知 ~10k chars 文档值）
- **V-7**：`/fork` 复制出的会话（v2.1.212+）其 sessionTitle 是否携带原名前缀？（携带 → fork 出的会话自动继承分区)

## 5. 本轮开放问题

| # | 问题 | 我的倾向 |
|---|---|---|
| Q-1 | shell 糖函数名 | **cz**（cc 会遮蔽 /usr/bin/cc 暗雷;cz 短、无冲突、区意明显） |
| Q-2 | 插件名 | 候选：**zoning**（城市规划中"功能分区"的本词，与插件理念同构）／ zones ／ quarter.目录现名 functional-partition-plugin 像占位符 | 
| Q-3 | MVP 边界 | M2=旗舰链路讨论区→核心区即 v0.1，其余链路排后——接受这个最小发布线吗 |
| Q-4 | 覆盖式 zone 定义 + `zone doctor` 校验 | 如上设计 |

**拍板（2026-09-07）：**

| # | 决定 |
|---|---|
| Q-1 | ✅ 糖名 `cz` |
| Q-2 | ✅ 插件名 `zoning` |
| Q-3 | ✅ M2（discuss→core 旗舰链路）= v0.1 最小发布线 |
| Q-4 | ✅ 覆盖式 zone 定义 + `zone doctor` 校验 |
