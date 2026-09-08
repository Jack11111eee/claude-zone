# zoning — Claude Code 功能分区插件

## What This Is

zoning 是一个 Claude Code 插件，为同一项目的会话引入「功能分区」维度：四个区（chore 杂活 / core 核心 / discuss 讨论 / maint 版本维护），每个区是一套会话画像（身份 prompt + 护栏 + handoff 模板 + 命名前缀 `--<zone> `）。区与区之间靠结构化 handoff 文档交接上下文，人确认后注入，模型永不代做决定。

## Core Value

不同性质的任务不共享同一个上下文——好情况无妨，坏情况污染上下文、结果偏移。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 四区会话画像：命名前缀（`--core `）+ SessionStart 前缀解析 + zone prompt 注入
- [ ] handoff 文档机制：/handoff 写作 → zone register 登记 → zone inject 消费（pending→consumed 生命周期）
- [ ] 补救路径：会话内 `/zone <zone>` 经 UserPromptSubmit hook 换区
- [ ] 护栏：discuss 锁 Write/Edit（allow_paths carve-out）、maint 拦高危 git、PreToolUse 拒绝
- [ ] 纯文件存储：repo `.claude/zones/*.yaml` 定义 + 本地 `~/.claude/zoning/<slug>/`（index.jsonl 事件流 + handoffs 目录）
- [ ] `zone` bin：纯 Python 标准库，which/list/pending/register/snapshot/inject/gc/doctor/show/title 子命令，全 --json
- [ ] 三入口：cz() 糖（主路径）、/zone 补救、/zones 巡视

### Out of Scope

- LLM 意图预判/自动跳转（D-002，用户明确撤回）— 交接以人确认为前提
- 对话全文索引/自动注入（claude-mem 教训）— handoff 是模型主动写的上下文包，不是事后压缩
- 收尾性 git 提醒（D-003）— commit/push/PR 留在工作会话
- 自定义第五区（P-6 封闭集合）— 架构支持但 v1 明确不开
- 沙箱级防护 — 护栏是威慑（防手滑），不防恶意
- TUI/GUI、SQLite、daemon、后台进程、云同步 — 状态全部可见即文件
- 与 session-finder 演进整合、与 GSD 插件整合（D-004/D-005）— 独立新作

## Context

- DESIGN.md v1.2（仓库根）是唯一权威（35 个拍板决策 + 16 项审查修复 + V-1~V-9 实验闭环）。实现细节一律照它办，不重新设计。
- 关键已验证事实：SessionStart stdin 含 session_title；`-n` 命名带 `--core` 前缀可行；命令文件存在是 slash 触发 UserPromptSubmit 的前提；additionalContext 注入完整（12k 实测）；按名 resume 必须等号形式 `--resume="--core x"`；Bash env 有 CLAUDE_CODE_SESSION_ID；/fork 不继承 title；UserPromptSubmit 不 block（A-2 裁决默认形态即最终形态）。
- 环境：Claude Code v2.1.263，macOS，zsh。用户偏好纯标准库、无第三方依赖、隐私敏感（handoff 不进 repo，留本地）。
- 实施模式：GSD Core 流程托管（本 .planning/ 目录），全自动推进（用户授权全部定夺）。

## Constraints

- **Tech stack**: bin 纯 Python 标准库（无 pip 依赖）；hooks 为薄封装调 `zone _` 内部子命令（M-5，同一逻辑单一实现）
- **Tech stack**: 插件脚手架按 §8.1（plugin.json/hooks.json/bin/skills/zones/README）
- **Storage**: repo 只放 zone 定义（.claude/zones/*.yaml 覆盖层）；handoff+索引在本地 ~/.claude/zoning/<project-slug>/
- **Compatibility**: 退出码 0/2/3/4；--json 全子命令；unzoned 会话零打扰（静默纯 CC）
- **Security**: 护栏=威慑不=沙箱；docotor 容忍并发 append（L-2）

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 35 项设计拍板（D/P/Q/R/A/B 系列）+ H/M/L 审查修复 | 六轮讨论收敛，DESIGN.md v1.2 定稿 | ✓ Good |
| M2=discuss→core handoff 全链路 = v0.1 | 旗舰功能垂直切片，先端到端走通 | — Pending |
| 垂直切片里程碑 M0~M5 | 横切先框架后填肉会长时间无可感知行为 | — Pending |
| GSD 托管实施：skill 调用被环境分类器阻断 → orchestrator 直接执行工作流 | 分类器间歇故障是环境问题；产物格式对齐 GSD 规范，流程不变形 | ⚠️ Revisit（若分类器恢复可切回 skill 调用） |

---
*Last updated: 2026-09-08 after project init (auto mode from DESIGN.md)*
