# zoning — Claude Code 功能分区插件

**不同性质的任务，不共享同一个上下文。**

Claude Code 的会话按项目目录组织（`/resume`），没有任务性质维度。zoning 补上这一维：一个项目四个区，每个区是一整套会话画像——身份（zone prompt）、护栏（guards）、交接（handoff 模板）、可见性（命名前缀）。

好情况时，混着的上下文无非有点乱；坏情况时，杂活的细节污染核心决策、讨论的头脑风暴带偏实施——**结果偏移**才是真代价。

## 四区

| 区 | 前缀 | 定位 |
|---|---|---|
| chore 杂活区 | `--chore` | 简单、一条线的杂活 |
| core 核心区 | `--core` | 复杂、非线性的构建/重构 |
| discuss 讨论区 | `--discuss` | 构建前的需求/架构讨论（禁改源码） |
| maint 版本维护区 | `--maint` | 维护性 git：分支清理、merge、tag（拦高危命令） |

## 三入口

| 入口 | 用法 |
|---|---|
| **主路径** | `cz core 任务名` → 起 core 区新会话（cz 糖见下） |
| **补救路径** | 会话中任何时候发 `/zone core` → 换区（title 补前缀、prompt 注入） |
| **巡视路径** | `/zones` → 按区分组看最近会话+未消费 handoff |

## 区之间怎么交接

**产物交接，不是意图预测。** 讨论末尾 `/handoff core` →模型把「值得带走的判断与状态」写成结构化文档（决策/开放问题/范围边界）→ 你在核心区新会话里看到提示行 → `/zone inject <id>` 注入并消费。模型可建议，永不代办：每个交接动作的目标会话、消费时机都是人定的。

```
discuss 会话 ──/handoff──▶ handoffs/core/ho-xxxx.md ──提示行──▶ core 会话
   决策与开放问题            （你确认后）inject            Next Steps 开工
```

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

数据位置（全部本地文件，无 daemon 无 SQLite）：

```
repo:  .claude/zones/*.yaml          # 区定义覆盖层（可团队共享）
本地:  ~/.claude/zoning/<slug>/      # handoff 文档 + index.jsonl 事件流（个人痕迹，不进 repo）
```

`ls` 就是诊断，重放就是重建。`zone doctor` 查一致性（孤儿/幽灵/命名错位）。

## 威慑非沙箱（必读声明）

**本插件的护栏是威慑级，不是沙箱。** Bash 锁不死（`echo x > file` 即绕过文件锁），PreToolUse 只能拦已知危险形态。目标是防误操作——讨论时手滑改了源码、维护时手滑 force-push——不是防恶意。真有恶意，任何插件级防护都是纸。

## 适用与不适用

- 适合：一人多线开发体验（讨论/实施/杂活/维护分头走）、想把「讨论结果不丢」工程化的人。
- 不适合：想全自动上下文魔法的人（D-002：本插件刻意不做意图预测与自动注入）。
