# 讨论稿 Round 02 — 核心机制细化

- 日期：2026-09-07
- 状态：✅ 已收口（P-1~P-6 全部拍板，见文末；命名语法修正见 round-03 §1）
- 上游：round-01（D-001 ~ D-006 已定）

---

## 0. 概念升级：区 ≠ 标签，区 = 会话画像（session profile）

如果四分区只做成"会话分组"，它就只是个带过滤器的文件夹。我建议升一级：**一个 zone 是一组声明式定义，进入该 zone 的会话获得一整套行为边界。**

```yaml
zone: core
prompt:      该区的身份与行为约束（注入的 zone prompt）
guards:      工具护栏（讨论区锁 Edit/Write；维护区拦截高危 git 命令）
mode:        建议权限模式（核心区联动 plan mode）
model:       建议模型档位（杂活 haiku / 核心 opus——仅建议，见开放问题 5）
prefix:      会话命名前缀（[chore] [core] [discuss] [maint]）
handoff_out: 退出时的产物模板（handoff 文档骨架，区而异）
handoff_in:  进入时的探测与注入规则
```

分区由此成为四件事的集合：**身份（prompt）× 护栏（guards/mode）× 交接（handoff）× 可见性（前缀）**。后文所有机制都挂在这四根柱子上。

---

## 一、进入机制：要不要 launcher 会话？

### 方案 A：裸启动 + 会话内 `/zone core` 切换

`cd project && claude` 进来，输入 `/zone core` 切入核心区。

- 问题①：进区前的杂聊已经污染了会话头部——AI 标题、首条消息摘要都从杂聊起算。
- 问题②：切换前进行的文件修改已发生，护栏没能从会话起点生效。

适合"临时巡视"，不适合当主路径。

### 方案 B：`claude -n "[core] 任务名"` 命名启动

- 优点：单一事实源（会话名即分区）、picker 原生可见（`/resume` 里搜 `[core]` 即可过滤）、`--resume <name>` 直接命中、零自建 UI。
- 缺点：依赖用户记得敲前缀；忘敲时需要补救路径。

### 方案 C（推荐）：命名启动为主 + `/zone` 补救 + `/zones` 巡视

- **主路径**：`claude -n "[core] 任务名"`。selector 起手即分区，护栏从首条消息生效。
- **补救路径**：忘了前缀 → 会话内 `/zone core`。技术上由 `UserPromptSubmit` hook 实现最稳：匹配到 `/zone <名字>` 的输入 → 写 `sessionTitle`（补前缀）+ `additionalContext`（挂 zone prompt）。这条 hook 路径是文档确认的能力（UserPromptSubmit 支持 sessionTitle 与 additionalContext）。
- **巡视路径**：`/zones` — 列出本项目各 zone 的未消费 handoff、最近会话、可复制的 resume 命令。

**结论：不需要 launcher 会话。** 三个入口都是语言层（命令/命名），无额外 UI、无额外会话。可选糖：shell 函数 `cc() { claude -n "[$1] ${@:2}"; }`，敲 `cc core 重构后端` 等价命名启动。（放 README 提示，不进插件本体。）

### "讨论完一键到核心区"（方一案的顺滑度保留）

讨论区会话做 handoff 时，顺带输出一条**深链**：

```
claude-cli://open?q=/zone inject ho-20260907-a1b2&q2=...&cwd=<项目绝对路径>
```

（深链打开新终端、prompt 预填不发送；`q` 的内容为"读取并注入 handoff <id> 并开始构建"形指令。）
新会话首条 prompt 即消费 handoff——人按一次键完成跳转，无自动跳转。

### 方案 C 的启动时序

```
claude -n "[core] 任务名"
  └ SessionStart (source=startup)
      ├ 从名称前缀解析 zone=core（无前缀 → 未分区，等 /zone 补救）
      ├ sidecar 登记：sessionId / cwd / zone / 时间 / 标题快照
      ├ 查 <handoff 目录>/core/ 下未消费 handoff
      └ 有 → stdout 提示行（SessionStart 的 stdout 直接入上下文）：
            "发现 2 条未消费 handoff：1) discuss 昨天《订单重构》决策4条/开放问题2 → /zone inject ho-xxx"
  └ 首条 prompt：/zone inject ho-xxx
      └ 命令解析 → 交付 handoff 全文 → 标记 consumed
```

### `/zone inject` 的实现载体（两选一）

- **(a) plugin bin 脚本（推荐）**：插件随 `bin/` 携带 PATH 可见的 `zone` 命令。`/zone inject <id>` 的命令正文指示模型执行 `zone inject <id>`（shell），脚本打印 handoff 全文（经 Bash 工具结果进入上下文）并原子更新 status 字段。**确定性交付**，不依赖模型解读。
- **(b) 纯话术**：命令正文是一段指令"读取 handoff 目录中 id 匹配 $ARGUMENTS 的文档并遵循它"，模型自己做 Glob/Read。少一个组件，但多一次模型自主寻路，且"标记已消费"还得模型自己 Edit。

推荐 (a)：命令就一个 Python 脚本（标准库），一并提供 `zone list` / `zone gc` 的底座。

**已核实的边界**：斜杠命令正文是静态 markdown，无法在展开时读文件——所以动态内容必须走脚本输出或 hook 注入，上面两条路都是绕开它的合法姿势。

---

## 二、handoff 的产出与生命周期

### 触发

```
/handoff                      → 交互选目的地 zone（AskUserQuestion，交互会话可用）
/handoff discuss              → 直接指定目的地
/handoff discuss "重新讨论状态管理方案"   → 带附注
```

命令展开为模板+写作指令，**模型在上下文完整时主动写出**——这是它区别于"事后压缩全文"（claude-mem 模式）的根本点。

### 文档骨架（模板 v1）

```markdown
---
id: ho-<yyyymmdd>-<短码>
from: discuss
to: core
session: <sessionId>
created: <ISO8601>
status: pending      # pending / consumed / stale
---
# <一句话标题>

## Intent 交接意图（一句话 + 触发场景）
## Decisions 已定决策
## Open Questions 开放问题
## Snapshot 现场（分支 / dirty 文件 / 涉及文件清单）
## Next Steps 建议的第一步
```

各 zone 的 `handoff_out` 模板差异（模板复用同一骨架，字段侧重不同）：

| 链路 | 侧重字段 |
|---|---|
| discuss → core | Decisions + Open Questions + 范围边界 |
| chore → discuss/core（升级） | **Why Escalated（为什么超纲）** + 现场（改到哪了） |
| core → discuss（暴雷回炉） | Blocked By + 具体问题清单 |
| core → maint（收尾） | Snapshot 全自动生成（git 分支拓扑 + log 摘要，**纯机器产物，不经 LLM**） |

### 生命周期（最小状态机）

`pending → consumed`（被 /zone inject 标记）；超 N 天（默认 14）未被消费 → `/zones` 列表中标灰为 `stale`。不做自动删除，`/zone gc` 手动清理——交接文档是人的思考痕迹，宁可堆积不可误删。

---

## 三、护栏的具体形状（与一个诚实的边界）

### discuss 区

- `PreToolUse(Write|Edit)`：deny，**除非路径在 `<handoff目录>/**` 之下**（写 handoff 本身必须放行——carve-out）。
- Bash：不锁（锁了什么都干不了）。zone prompt 里声明"讨论不动手"。

### maint 区

- `PreToolUse(Bash)`：模式匹配拦高危命令（`push --force`、`reset --hard`、`branch -D`、`clean -fd`…），白名单形护栏——**拦截高危而非枚举全部安全命令**（后者无法穷举且会误伤）。
- Write/Edit：对代码文件 deny（维护会话改的是 git 状态，不是代码；若确实要改 .gitignore 等，条目本来就属于配置文件，可单独放行）。

### core 区

- 默认建议 plan mode 起步（`claude --permission-mode plan` 或提示用户 Shift+Tab），zone prompt 声明"先计划后动手"。

### 诚实边界（必须写进 README）

**护栏是威慑级，不是沙箱。** Bash 无法被完全锁死（`echo x > file` 就能绕过文件锁），PreToolUse 的模式匹配也只能拦已知危险形态。分区护栏的目标是**防误操作**（讨论时手滑改文件、维护时手滑 force-push），不是防恶意。

---

## 四、存储位置（待拍板 P-1）

| | 方案甲：全放 repo `.claude/zones/` | 方案乙：全放本地 `~/.claude/` 下 | 方案丙（推荐）：分而治之 |
|---|---|---|---|
| zone 定义（四区 profile，声明式 yaml） | ✅ 团队共享、可版本化 | ❌ 每人一张桌 | ✅ repo |
| handoff 文档 | ⚠️ 讨论内容进仓库（隐私、体积、AI 思考痕迹公开） | ✅ 个人工作台 | ✅ 本地 |
| sidecar 索引 | ⚠️ 多人多机会互踩 | ✅ 个人 | ✅ 本地 |

推荐理由：定义是**配置**（像 .editorconfig），交接是**个人痕迹**（像 shell history）。跨机器同步交给用户自己的云盘/rsync，不做进插件（第一版不做云）。

---

## 五、可见性：sidecar 索引

- 索引行：`{sessionId, zone, title_snapshot, created, lastSeen}`——标题自存快照，防会话 JSONL 被官方 30 天清理后指针悬空。
- `/zones` 渲染：按 zone 分组 → 最近会话 + 未消费 handoff 数 + 复制即用 `claude --resume <name|id>`。
- 原生借力：用户在 `/resume` 里键入 `[core]` 搜索即为分区过滤——**不重建 UI，借力 picker 的搜索框**。

---

## 六、负空间（明确不做）

1. LLM 意图预判 / 自动跳转（D-002）
2. 对话全文索引 / 自动注入（claude-mem 教训）
3. 收尾性 git 提醒（D-003）
4. TUI / GUI 外壳（既无必要也违背纯插件定位）
5. SDK `tag_session`（CLI 不显示 tag，sidecar 替代）
6. 修改原生 /resume UI（无扩展点）

---

## 七、本轮问题与拍板（2026-09-07，六项全拍）

| # | 问题 | 我的倾向 |
|---|---|---|
| P-1 | 存储分而治之（定义 repo、handoff+索引本地）？ | 推荐方案丙 |
| P-2 | `/zone inject` 走 plugin bin 脚本（方案 a）？ | 推荐 a |
| P-3 | 讨论区 Write 的 carve-out（放行 handoff 目录）+ "护栏是威慑不是沙箱"的边界声明？ | 两者都要 |
| P-4 | handoff 三态生命周期（pending/consumed/stale）+ 手动 gc？ | 推荐如上 |
| P-5 | zone 定义中的 model 档位：CC 无按会话强制模型的插件接口，只能写进 prompt 当建议，或在启动时由用户带上 `--model`（可并入 shell 糖 `cc()`）。接受降级为"建议"吗？ | 建议 + cc() 糖 |

**拍板结果：**

| # | 决定 |
|---|---|
| P-1 | ✅ 存储分治（方案丙）：zone 定义进 repo `.claude/`，handoff 文档与 sidecar 索引留本地 `~/.claude/` 下 |
| P-2 | ✅ `/zone inject` 走 plugin bin 脚本（`zone` 命令，纯 Python 标准库，含 list/gc 底座） |
| P-3 | ✅ 讨论 Write carve-out（放行 handoff 目录）与"威慑非沙箱"声明，两者都要 |
| P-4 | ✅ handoff 三态（pending/consumed/stale）+ 不自动删 + 手动 gc，两者都要 |
| P-5 | ✅ model 档位降级为 prompt 建议 + `cc()` shell 糖（接受降级） |
| P-6 | ✅ 四区封闭集合；架构预留（声明式定义天然支持），"此刻"明说不开自定义 |

**命名语法用户反馈**：`claude -n "[core] 任务名"` 的引号影响输入，要求去掉——升级处理为 round-03 §1（glob 冲突硬理由，见该轮）。
