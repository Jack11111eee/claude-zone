# zoning — Claude Code 功能分区插件

**不同性质的任务，不共享同一个上下文。**

Claude Code 的会话按项目目录组织（`/resume`），没有任务性质维度。zoning 补上这一维：一个项目四个区，每个区是一整套会话画像——身份（zone prompt）、护栏（guards）、交接（handoff 模板）、可见性（命名前缀）。

好情况时，混着的上下文无非有点乱；坏情况时，杂活的细节污染核心决策、讨论的头脑风暴带偏实施——**结果偏移**才是真代价。

三条底层原则（编号可溯源 DESIGN.md）：

- **提示≠注入**（D-002）：插件可以提示「有未消费的 handoff」，但注入与否、何时注入、进哪个会话，永远是人决定的。模型可建议，永不代办。
- **状态全部是文件**：无 SQLite、无 daemon、无后台进程。`ls` 就是诊断，重放就是重建。
- **脚本是哑管道**：`zone` 永远不知道「该不该 handoff」——它只知道有谁、在哪、什么状态。智能都在模型侧。

**目录**：[四区](#四区) · [三入口](#三入口) · [命令清单](#命令清单) · [讲解](#讲解) · [cz() 糖](#cz-糖) · [安装](#安装) · [威慑声明](#威慑非沙箱必读声明) · [适用与不适用](#适用与不适用)

## 四区

| 区 | 前缀 | 定位 | 护栏 |
|---|---|---|---|
| chore 杂活区 | `--chore` | 简单、朴素、一条线的杂活：改文档、修局部 bug、数据备份 | 无 |
| core 核心区 | `--core` | 复杂、非线性、可能引出更多问题的构建/重构 | 无（prompt 建议 plan mode 起步） |
| discuss 讨论区 | `--discuss` | 构建前的需求/架构讨论、方案细化 | 禁 Write/Edit（handoff 文档除外） |
| maint 版本维护区 | `--maint` | 维护性 git：分支清理、merge、gitignore、远程、tag | 禁改码 + 拦高危 git 命令 |

- 四区是**封闭集合**（P-6）：不可增删分区。架构上扩展没有障碍，但「此刻」明说不开自定义。
- **维护性 ≠ 收尾性**（D-003）：commit/push/PR 等收尾动作留在工作会话内完成，zoning 不提醒、不代办；分支清理、merge、gitignore、tag 才是 maint 区的事。
- model 档位（chore=haiku、core=opus）是建议不是强制（P-5），落实在 cz() 糖里，不想用删两行。

## 三入口

| 入口 | 用法 | 什么时候用 |
|---|---|---|
| **主路径** | `cz core 任务名`（＝`claude -n "--core 任务名"`） | 起手就知道任务性质，按区起会话 |
| **补救路径** | 会话内任何时候发 `/zone core` | 忘了分区、中途跑偏、/clear 后想把区身份捡回来 |
| **巡视路径** | `/zones` | 看各区分头进行到哪了（只读） |

- 判定规则只有一条：会话标题以 `--<zone> ` 开头（zone 恰为四区之一）→ 属该区。残留 `[core]` 旧语法会自动归一化为 `--core`——方括号是 shell glob 字符类，zsh 下会报 `no matches found`，弃用有硬理由。
- 没有前缀的会话 = **unzoned**：插件零打扰（不注入、不拦截、不提示）。「没选区的人不受管」。
- **按名 resume 必须等号形式**：`claude --resume="--core 任务名"`；空格分离形式会被 CLI 当未知 flag 报错（V-3 实测）。

## 命令清单

三层命令面：终端层（起会话）、会话内层（`/` 命令）、CLI 层（`zone` 子命令，会话内外都能跑）。

### 终端层：起会话

| 命令 | 作用 |
|---|---|
| `cz <zone> 任务名` | 起该区新会话（零引号；chore→haiku / core→opus 档位映射在糖里） |
| `claude -n "--core 任务名"` | 主路径裸形态：`-n` 直接定标题，前缀即分区 |
| `claude --resume="--core 任务名"` | 按名回到该区会话（务必等号形式，见上） |
| `claude-cli://open?q=%2Fzone%20core&cwd=<URL 编码>` | 深链：开新会话、prompt 预填 `/zone core` **不发送**——人按发送键才算落区 |

深链的 `q` 是 `/zone <目标区>` 的 URL 编码（固定形态如 `%2Fzone%20core`）；`/handoff` 登记成功后会自动给你生成现成的。

### 会话内：/ 命令

| 命令 | 作用 |
|---|---|
| `/zone <zone>` | **换区**：title 补前缀、索引登记、注入目标区 prompt、探测未消费 handoff，一步到位 |
| `/zone` | 无参：模型用选择器让你四选一，再提示你发送 `/zone <zone>`——落区这一下留给人 |
| `/zone inject <id>` | **消费 handoff**：文档全文进上下文，状态 pending→consumed |
| `/handoff` | 写交接文档并登记（目标区缺省时交互四选一） |
| `/handoff core` | 直接指定交给 core |
| `/handoff core "附注"` | 带一句话附注（写进文档 Intent 段的触发场景） |
| `/zones` | 巡视总览（只读）：按区分组看最近会话 + 未消费 handoff，尾部附可复制的恢复命令 |

三个都是插件 skills。`/zone <zone>` 的本体逻辑在 UserPromptSubmit hook 里，skill 只是占位——占位本身是功能必需：不存在的命令在扩展期直接被拒，hook 根本不会触发（V-5）。

### CLI 层：zone 子命令

`zone` 是插件唯一可执行（`bin/zone`，纯 Python 标准库，会话内已在 PATH）。在项目根跑，cwd 即项目定位依据。

| 子命令 | 作用 | 输出 | 写操作 |
|---|---|---|---|
| `zone which [--session <id>] [--cwd <path>]` | 查会话属于哪个区 | `core` 或 `unzoned` | 否 |
| `zone list [--zone=Z]` | 会话 + handoff 全量摘要（含已消费、幽灵行，如实报告） | 两张表 | 否 |
| `zone pending [--zone=Z]` | 仅未消费 handoff = 目录扫描 ∩ 索引状态 | 表格 | 否 |
| `zone register <file>` | 校验 frontmatter 合法 → 登记为 pending（重复登记是安全 no-op） | `registered <id>` | 是 |
| `zone inject <id> [--force]` | 打印全文并标记 consumed | 文档全文 | 是 |
| `zone snapshot` | 生成 git 现场块：当前分支 / porcelain / log -5 / 分支清单（纯机器产物，不经 LLM 改写） | markdown 块 | 否 |
| `zone gc [--stale-days=14]` | 过期（created 起 14 天，不论是否已消费）的 handoff 移入 `.trash/` | `moved N, kept M` | 是（只移不删） |
| `zone doctor` | 体检：zone 定义合法性 + 存储一致性（孤儿/幽灵/命名错位/索引坏行） | 问题清单或 `OK` | 否 |
| `zone show <zone>` | 该区最终合并定义（内置 ∩ repo 覆盖层） | yaml | 否 |
| `zone title <title>` | 前缀判定 + `[zone]` 旧语法归一化 | `zone: core, rest: …` | 否 |

通用约定：

- 全部子命令支持 `--json`：输出单行 JSON（`{"ok":true,"v":1,"cmd":…,"data":…}`），机器消费走它。
- 退出码：`0` 成功；`2` 用法错误；`3` 找不到匹配的 handoff（未登记、已消费默认拒绝、幽灵）；`4` zone 定义非法。`doctor` 恒 `0`——问题看输出，不靠退出码。
- `which` / `inject` 会话内免参（自动读 `CLAUDE_CODE_SESSION_ID`）；外部终端诊断加 `--session <id>`。
- `inject` 已消费文档默认拒绝（exit 3），`--force` 是逃生门（`/clear` 后回看、新会话重读决策）：追加 `re_consumed` 事件，状态只前进不回退（P-4）。

## 讲解

### 主路径：会话启动时发生什么

```
cz core 重构订单表
  = claude -n "--core 重构订单表"
  └ SessionStart hook（薄封装，逻辑都在 zone bin）
      ├ 解析标题前缀 → zone=core（无前缀 → unzoned，一切免打扰）
      ├ 索引登记：index.jsonl 追加一条 session 事件
      ├ 注入 zone prompt（additionalContext，会话身份）
      └ 探测 handoffs/core/ 未消费 handoff → 提示行（如有）：
        「核心区已就绪。未消费 handoff：1) 订单重构决策 → /zone inject ho-xxx」
```

- **提示≠注入**：只告诉你有什么，全文要你亲手 `/zone inject`。
- subagent / skill 上下文不登记（不是主会话，不来添乱）。
- 会话结束时 SessionEnd hook 补一条 lastSeen，让 `zone list` 的相对时间保持新鲜。

### 补救路径：/zone 换区

会话跑偏了（聊着聊着发现该写代码了，或 `/clear` 后区身份丢了）：发 `/zone core`。

- 语义是**追加**一条索引事件——同 sessionId 后事件覆盖前事件，历史不重写、来源可审计（`source: "command"`）。
- 标题同时打上前缀：名字取本会话首条用户消息（截 ~40 字），取不到用日期兜底。
- 换完同样注入目标区 prompt + 探测该区未消费 handoff——与启动同口径。
- 无参 `/zone`：模型用选择器问你 → 你选 core → 模型回复「请发送 `/zone core`」→ 你按发送。这一个回车是保留给人的确认动作，不是模型代办。

### 巡视路径：/zones

只读命令：跑 `zone list` + `zone pending`，按区分组渲染最近会话与未消费 handoff，空区隐藏。尾部直接给可复制的恢复命令（一律等号形式，可加粗警告提醒）与深链。未消费 handoff 的消费（inject）由你在目标区会话里自行发起——巡视是看，不是动。

### /handoff：一次完整交接

```
discuss 会话 ──/handoff core──▶ handoffs/core/ho-xxxx.md ──提示行──▶ core 会话
   决策与开放问题                 （登记成功）             /zone inject   Next Steps 开工
```

1. 在 discuss 会话内发 `/handoff core "重新讨论状态管理"`（附注可省）。
2. 模型趁上下文还热，按模板把「值得带走的判断与状态」写成结构化文档，**直接写最终路径** `~/.claude/zoning/<slug>/handoffs/core/ho-<日期>-<4码>.md`。
3. 模型立即 `zone register <file>`：frontmatter 校验通过才入册——**写入=登记**原子成立（M-1）。校验失败它会按报错修复后重新登记（闭环在模型侧）。
4. 模型输出 `registered <id>` + 现成的深链。
5. 你在 core 区新会话（或现会话 `/zone core` 后）看到提示行 → `/zone inject ho-xxx` → 全文进上下文，消费完成。

**产物交接，不是意图预测。** 模型写的是判断与状态（决策/开放问题/范围边界），不是聊天记录搬运；目标会话、消费时机都是人定的。

### handoff 文档长什么样

frontmatter（机器层，register 按此校验）+ 正文（人机共享层，`#` 标题起供人读）：

```markdown
---
id: ho-20260908-a1b2          # ho-<yyyymmdd>-<4位随机码>，口述友好
from: discuss                  # 来源区（unzoned 也允许）
to: core                       # 目标区 ＝ 所在目录 handoffs/core/
created: 2026-09-08T14:30:00+08:00
tags: []                       # 预留，v1 不消费
---

# 一句话标题（会出现在提示行里，写得能认出这是哪件事）

## Intent           交接意图：一句话 + 触发场景（用户附注写在这里）
## Decisions        已定决策：编号列表，每条「决定 + 理由」
## Open Questions   开放问题：目标区要回答/拍板的
## Snapshot         现场：分支 / dirty 文件 / 涉及文件清单（如实，不美化）
## Why Escalated    为什么超纲——仅 chore→core/discuss 升级链使用，其余省略
## Next Steps       建议的第一步：具体可执行
```

按链路侧重取舍详略（模板矩阵，不写死路由）：

| 链路 | 侧重 |
|---|---|
| discuss → core | Decisions + Open Questions + 范围边界（末条明示「做什么、不做什么」） |
| chore → core / discuss（升级） | **Why Escalated**（为什么超纲）+ Snapshot（改到哪了） |
| core → discuss（暴雷回炉） | Open Questions 以 Blocked By + 具体问题清单为主；Decisions 记已试过与已排除的 |
| core → maint（收尾） | Snapshot 先跑 `zone snapshot`，机器输出**原样嵌入**，不加评论不改写 |

杂活↔杂活、任何形式的对话全文搬运：明确不做（负空间）。

### handoff 生命周期与 gc

```
pending ──inject──▶ consumed               # 调用即消费
consumed ──inject --force──▶ re_consumed    # 状态只前进，不回退
pending ──created 起 14 天──▶ (stale)        # 渲染时派生显示，非存储状态
任何状态 ──zone gc──▶ handoffs/.trash/       # 物理移动，永不删除
```

- 跨区消费允许（B-1）：handoff 只是上下文包，注入不限于收件区，索引如实记谁消费的。
- stale 判定以 `created` 起算，与是否消费无关；`--stale-days=N` 可调阈值。
- **宁可堆积，不可误删**：gc 只把过期文档挪进 `.trash/`（同名冲突加 `-1/-2` 尾缀），清不清空 trash 是人的事。交接文档是思考痕迹。

### 护栏：拦什么，放什么

| 区 | Write/Edit | Bash |
|---|---|---|
| chore / core | 放行 | 放行 |
| discuss | **禁**（白名单 `**/handoffs/**`：讨论的终点是写 handoff，不是改源码） | 放行 |
| maint | **禁**（白名单：handoff 文档、`.gitignore`、`.claude/zones/**`） | **拦已知危险形态** |

maint 的 Bash 黑名单默认七条正则（L-6，拦的是形态不是命令名）：

- `git push --force`（含多空格等形态；`--force-with-lease` 是保护性操作，放行）
- `git reset --hard`
- `git branch -D` / `git branch --delete --force`
- `git clean` 带含 `f` 的组合旗标（`-fd`、`-Xfd`…；`-n` 干跑不误伤）
- `git checkout <目标> -- <路径>`（路径级丢弃）
- `git reflog expire`、`git gc --prune=now`

判区一律按 sessionId 查索引；**无会话 id / 未登记（unzoned）→ 一律放行**（degrade-to-open：护栏只对主动选区的会话生效，插件自身出问题永不拦住你的工作）。

### 自定义 zone 定义（repo 覆盖层）

repo 里放 `.claude/zones/<zone>.yaml` 可**字段级覆盖**内置默认（方向：repo 覆盖插件，深合并），比如让 discuss 顺手也能写 docs：

```yaml
# .claude/zones/discuss.yaml
guards:
  allow_paths:
    - "**/handoffs/**"
    - "docs/**"
```

- 只可覆盖已列出字段（`prompt` / `guards` / `inject_on_entry` / `model_hint` 等）；未知字段 → `zone doctor` 报错、`zone show` exit 4，不静默降级（B-6）。
- 不可增删分区（P-6）：出现第五区名 → doctor 警告，该文件不生效。
- 该目录进 repo 可团队共享（配置如 .editorconfig）；handoff 数据在 `~/.claude/` 属个人痕迹，不进 repo。

### 存储与诊断

```
repo:  .claude/zones/*.yaml          # 区定义覆盖层（可团队共享）
本地:  ~/.claude/zoning/<slug>/      # slug = 项目绝对路径非字母数字逐字符换 -
         index.jsonl                  # append-only 事件流（会话登记/换区/handoff 生命周期）
         handoffs/<zone>/<id>.md      # 按 to 分目录（收件箱视角）
         handoffs/.trash/             # gc 产物
```

- `ls` 就是诊断，重放就是重建。索引是纯文本 jsonl（每事件 ~200B，千会话量级 ≈ 2MB），`zone list` / `zone pending` 直扫，无数据库。
- `zone doctor` 查四类不一致：**孤儿**（有文件无登记——手工 `zone register` 补）、**幽灵**（有登记无文件——inject 时 exit 3）、**命名错位**（frontmatter.to ≠ 所在目录）、**索引坏行**（并发写碰撞残留）。只报告不修复——修复动作永远是人执行的，机器不猜状态。

### hook 架构（一句话）

五个 hook（SessionStart / UserPromptSubmit / PreToolUse×2 / SessionEnd）全部是薄封装（M-5）：解析、登记、探测、判区的逻辑一律在 `zone` bin 的内部子命令里，hook 自身不含业务逻辑——同一逻辑单一实现，hook 与 CLI 永不漂移。

## cz() 糖（README 提供，不进插件本体）

```bash
# ~/.zshrc
cz() {
  local m
  case "$1" in
    chore)   m=haiku ;;           # zone→model 映射（档位是建议，不想用删这两行）
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

糖名取 `cz` 不取 `cc`：`cc` 是 `/usr/bin/cc`（clang），遮蔽它是埋暗雷。

## 安装

```bash
claude plugin marketplace add <本仓库路径或 marketplace 引用>
claude plugin install zoning@zoning
```

版本：v1.1.0（版本号自 v1.1 起语义化）。v1.0 = 全量功能交付；v1.1 = hook 文案单源化、SessionEnd lastSeen、护栏加固（`git clean` 组合旗标与多空格形态）。

## 威慑非沙箱（必读声明）

**本插件的护栏是威慑级，不是沙箱。** Bash 锁不死（`echo x > file` 即绕过文件锁），PreToolUse 只能拦已知危险形态。目标是防误操作——讨论时手滑改了源码、维护时手滑 force-push——不是防恶意。真有恶意，任何插件级防护都是纸。

## 适用与不适用

- 适合：一人多线开发体验（讨论/实施/杂活/维护分头走）、想把「讨论结果不丢」工程化的人。
- 不适合：想全自动上下文魔法的人（D-002：本插件刻意不做意图预测与自动注入）。
