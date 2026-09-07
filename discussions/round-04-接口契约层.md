# 讨论稿 Round 04 — 接口契约层

- 日期：2026-09-07
- 状态：🔴 OPEN（待反馈，重点 R-1 / R-3 / R-6）
- 上游：round-03（Q-1~Q-4 已定：cz / zoning / M2=v0.1 / 覆盖式 zone 定义）
- 本轮地位：**设计梁柱的最后一轮**——契约敲定后，总设计文档（唯一权威）即可从 round-01~04 汇编

---

## 0. 契约总览（三轮谈判后的最终形状）

```
用户 ──cz / claude -n──▶ [zoning 会话]
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
   zone bin 脚本          hooks                    /命令
   (zone ... 子命令)   (SessionStart 等)      (/zone /handoff /zones)
        └─────────────────────┴──────────────────────┘
                     │
        ▼ 读写两处状态（P-1 分治）
  repo: .claude/zones/*.yaml     ← zone 定义（可覆盖式）
  本地: ~/.claude/zoning/        ← sidecar 索引 + handoff 文档
        ├── index.jsonl         ← 索引（append-only）
        ├── handoffs/<zone>/<id>.md
        └── logs/? （暂不引入，负空间）
```

设计律：**脚本只是读写状态的哑管道；智能（prompt、判断、写作）都在模型侧。** 脚本永远不知道"该不该 handoff"，它只知道有谁、在哪、什么状态。

---

## 1. `zone` bin 子命令集与输出契约

> 命令名 `zone`（placeholder，R-1 待拍板），入口统一 `zone <subcommand>`，纯 Python 标准库，参数风格走 POSIX 风格短横线。

| 子命令 | 语义 | stdout 契约（面向模型/人可读） |
|---|---|---|
| `zone which` | 当前会话属于哪个区 | `core` 或 `unzoned`（单行纯文本）|
| `zone list [--zone=Z]` | 列 handoff 与会话索引摘要 | 人读表格：（id、状态、标题、from→to、相对时间）|
| `zone pending [--zone=Z]` | 只列未消费 handoff | 同上，仅 pending |
| `zone inject <id>` | 打印 handoff 全文；status pending→consumed | 文档全文（frontmatter+正文）|
| `zone gc [--stale-days=14]` | 将 stale 文档移入 trash/ 子目录（不直接删） | 汇总行：`moved N, kept M` |
| `zone doctor` | 校验 zone 定义合法性（第五区名、字段类型） | 问题清单或 `OK` |
| `zone show <zone>` | 查某区定义（合并插件默认+repo 覆盖后的最终视图） | 合并后的 yaml |
| `zone title <title>` | 归一化+校验标题（`[core]`→`--core`；判前缀） | 解析结果 `zone: core, rest: 重构后端` 或 `unzoned` |

- `inject` 是**唯一 mutating 命令**（写 status 与索引）；`gc` 移入 trash/ 待人工清空——加上"不自动删"原则，数据永远不无中生有地消失。
- 所有子命令 `--json` 输出机器可读版（hook 内部调用、未来扩展用），默认人读表格。契约：JSON schema 见附录 A。
- 退出码：0 成功；2 用法错；3 找不到匹配的 handoff；4 定义非法。

> 插件 bin 与 CC 的 Bash 工具 PATH：文档确认插件 `bin/` 目录在会话内 PATH 可见——脚本经 Bash 调用无问题。**注意**：claude CLI 本体必须在常规 PATH（cz 无脑从用户 shell 里跑,均为常规进程）。

---

## 1b. 状态文件格式（两个候选，R-1b）

P-2 拍板了 plugin bin 跚本。底座状态存两个候选：

- **(a) 纯文件铁律（推荐）：可见即文件——`.claude/zones/` 的 yaml、handoff 目录、index.jsonl**。无 SQLite、无 daemon、无后台进程。`git grep -r "--core" .` 或 `ls` 即全局透明。诊断=看文件。用户的纯标准库偏好自然延伸。
- (b) SQLite（claude-mem 路线）：查询强，但引入 daemon/锁/损坏面/"黑盒感"，与"个人痕迹"的温度感冲突。

推荐 (a)。但**索引查询**仍需焦点讨论（R-3）：纯文件的代价是磁盘扫描（O(目录遍历)），会话多了（几百上千）`zone list` 会变慢——查询始终限定在单一索引 jsonl（KB~MB 级）内做过滤聚合，不遍历会话目录，不构成矛盾。

---

## 2. sidecar 索引行 schema（index.jsonl，append-only）

```jsonc
// 每行一个事件，不是每会话一行——append-only 事件日志，重建=从头重放
{"ts": "2026-09-07T17:20:00+08:00",  "type": "session", "sessionId": "<uuid>", "zone": "core", "title": "--core 重构后端", "cwd": "<abs>", "source": "prefix|command|auto"}
{"ts": "...", "type": "handoff", "id": "ho-20260907-a1b2", "from": "discuss", "to": "core", "status": "pending", "title": "订单重构决策"}
// status 变更也append 新事件，同 id 的最后一条即现值
{"ts": "...", "type": "handoff", "id": "ho-20260907-a1b2", "status": "consumed", "by": "<sessionId>"}
```

字段说明：

- `source`: `prefix`（cz 起）| `command`（/zone 补救）| 其他留空（跳转场景留待以后）——分区归属的可审计来源。
- handoff 状态查现值规则：**同 id 的最后一条事件为准**（事件溯源最小实现）——不更新旧行，不重写历史。
- 体积预估：每事件 ~200B，千会话×十事件 ≈ 2MB 纯文本 jsonl，无性能问题。重建索引=重放（`zone reindex` 内部逻辑，不暴露 CLI 子命令名,保底修复手段）。

---

## 3. handoff 文档 schema v1（定稿候选）

```markdown
---
id: ho-<yyyymmdd>-<4h>          # 随机短码，碰撞概率忽略
from: discuss
to: core
created: 2026-09-07T17:20:00+08:00
consumed: null                   # 注入时由 zone inject 回写
consumed_by: null
tags: []                         # 预留，v1 不消费
---

# <一句话标题>

## Intent       交接意图（一句话+触发场景）
## Decisions    已定决策（编号列表）
## Open Questions  开放问题（编号列表）
## Snapshot      现场（分支/dirty 文件/涉及文件清单）
## Why Escalated 为什么超纲（仅升级链路使用，其他链路省略）
## Next Steps   建议的第一步
```

规则：

- **frontmatter 是机器层；从 `# 标题` 起是人机共享层**——`zone inject` 打印全文，模型不需要解析 frontmatter 也能照 Next Steps 行动（frontmatter 的 from/to 等元数据会以导语形式一并可见）。
- 专属字段 `Why Escalated` 只出现在 chore→core/discuss 链路；`core→maint` 链路 Snapshot 为纯机器生成（git log 拓扑+分支状态)。
- 段落缺失容忍：模板字段未填不报错，`zone doctor` 只检查 id/from/to/created/status 存在性。
- ID 时间可读性：`ho-20260907-a1b2` 年月日+4 位随机码日常口述友好（"inject 一下昨天那个订单的 ho"）。

---

## 4. zone.yaml 字段级规格（覆盖式合并的基准）

```yaml
# 插件内置默认（repo 覆盖层同 schema，仅可覆盖列出的字段）
name: core
display: 核心
prefix: --core
prompt: |
  本会话处于核心区。……（M1 敲定的正文）
mode_hint: plan            # 仅建议：写入启动提示
model_hint: opus           # 仅建议（P-5 降级）
inject_on_entry:
  zone_prompt: true
  pending_handoff_scan: true   # 探测未消费 handoff（to=本区）
guards:
  # PreToolUse matcher
  deny_write_edit: false       # discuss 区 true（handoff 目录 carve-out 在 hook 逻辑中实现，不占字段）
  bash_block_patterns: []      # maint 区准入高危命令模式（事件 hook 匹配）
  allow_paths:                # Write/Edit carve-out 白名单
    - "**/handoffs/**"
handoff_out: discuss_to_core   # 引用模板名
handoff_in: standard
```

- repo 覆盖层规则（round-03 §3 已拍）：**只可覆盖字段值，不可增删分区**；`zone doctor` 发现第五区名或未知字段→报错。
- `guards.deny_write_edit=true` 的实现位置：PreToolUse hook 读当前会话 zone（从 sidecar 索引 by sessionId）→ decide。**不是**从 cwd 推断——同一个 repo 里多个并行会话可能不同 zone（worktree/多终端场景），源真相在索引。
- 覆盖式判定合并方向：**repo 覆盖插件默认**，hook 启动时读入合并，运行期不热重载（会话生命周期内稳定，重启生效）。

---

## 4b. hooks 清单（谁在什么时机干什么）

| hook | matcher | 做什么 | 不做什么 |
|---|---|---|---|
| SessionStart | startup/… | 解析前缀→登记索引→探测 pending handoff→ **stdout 提示**（不注入）、zone prompt 经 additionalContext 注入 | 不自动注入 handoff 全文；不改 title（保留用户命名权） |
| UserPromptSubmit | all | 拦截 `/zone core` 目录式输入→走补救路径（sessionTitle+zone prompt） | 不侦察普通消息 |
| PreToolUse | Write/Edit | 该区 deny_write_edit=true 时 deny（handoff 目录 carve-out） | — |
| PreToolUse | Bash | 该区 bash_block_patterns 命中时 deny | — |
| SessionEnd | — | 轻量更新 lastSeen | 不做 LLM 分类（D-002 精神） |

主线不做 SessionEnd 内容分析。会话归档归属以 SessionStart 前缀为源真相，**事后归属跃迁**（用户手动 `/zone maint` 换区已覆盖）。

## 5. /命令清单与分工（模型侧智能所在）

| 命令 | 干什么 | 与 zone bin 的关系 |
|---|---|---|
| `/zone` | 无参=交互选区（补救路径）；`/zone inject <id>` 同义复合 | prompt 引导模型调 `zone inject` |
| `/handoff` | 模板+写作指令，模型写 handoff | 写完调 `zone register`（R-2）登记索引 |
| `/zones` | 全局巡视总览 | 调 `zone list` 渲染 |

`/handoff` 的命令正文不写死 "discuss→core"，模板按 **当前区** (zone which) × **目标区** (用户参数) 选择，四区组合自动覆盖全部链路，同一模板骨架不同侧重（round-02 §2 表）。

---

## 6. 正交性最终检验（四根柱子 × 机制交叉）

|  | 身份 prompt | 护栏 guards | 交接 handoff | 可见前缀 |
|---|---|---|---|---|
| SessionStart | ✅注入 | ✅读表 | ✅探测 | ✅解析 |
| PreToolUse | — | ✅decide | — | — |
| /handoff | ✅写作指令 | — | ✅产出 | — |
| zone bin | ✅ show | ✅ doctor | ✅ register/inject/gc | ✅ list render |
| `/resume` picker | — | — | — | ✅原生搜索 `--core` |

机制与柱子无耦合死角；每根柱子至少有两个承载点（冗余）与单一事实源（索引/定义/文档）。

---

## 7. 本轮开放问题

| # | 问题 | 我的倾向 |
|---|---|---|
| R-1 | bin 命名 | **`zone`**（动词化自然：zone inject/list/doctor；gsd 系多为 gsd- 前缀，无撞名风险） |
| R-2 | `/handoff` 写完后是否自动 `zone register` | **推荐自动**：模型写完文档后自动调用登记（多一步 confidence check：register 脚本校验 frontmatter 合法才入册——**写入=登记**原子成立，手滑少一步） |
| R-3 | 索引查询的实现债：jsonl 重放 vs SQLite | **推荐 jsonl+重放**——几 MB 级无性能问题、纯文件铁律的可审计性价值 > 查询性能（会话上千再议，YAGNI） |
| R-4 | inject 时 consumed 事件的 `by` 字段记 sessionId 还是记录人 | sessionId（机器层事实），人名不做（多人共用同一台机器不在场景内） |
| R-5 | `zone inject` 是否需要 `--force` 消费一个 consumed 状态的文档 | **支持**：re-inject 已消费文档是合法场景（例如原会话 /clear 后想回看；scene: "进入新会话再读一遍上次的决策"）。默认拒绝+`--force` 逃生门，且 status 不回退（历史事件 append `re_consumed`） |
| R-6 | 本轮契约（§1 ~ §6）整体 | 可作为总设计文档的直接骨架 |

> R-2 的自动登记是唯一"模型行为不可靠"风险点：register 校验失败时命令正文会提示模型自行修复 frontmatter——闭环留在模型侧。
