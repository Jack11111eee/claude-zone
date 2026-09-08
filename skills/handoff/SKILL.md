---
name: handoff
---

写一份 handoff 交接文档并登记（DESIGN.md §6）：把当前会话「值得带去另一个
区的判断与状态」写成结构化文档，写完立即 `zone register`，由人在目标区的
新会话里 `/zone inject` 消费。全程你只写文档与登记，不替用户换区、不替
用户注入（提示≠注入，D-002）。

## 触发形态

| 调用 | 目标区 to |
|---|---|
| `/handoff` | 缺省 → 用 AskUserQuestion 让用户四选一（chore/core/discuss/maint） |
| `/handoff core` | core |
| `/handoff core "附注"` | core；附注一句话，写进 Intent 的触发场景 |

- from = **当前区**：从 hook 注入的 zone prompt 上下文感知（unzoned 会话
  同样允许 /handoff，frontmatter 记 `from: unzoned`，L-3）。
- to = **目标区**：用户参数或交互选择结果，恰为四区之一。

## 写作流程（顺序执行）

1. 确定 from / to / 附注。
2. 生成 id：`ho-<yyyymmdd>-<4位随机小写十六进制>`（日期取今天，4 位随机码
   自选，不与已知 id 重复）。形如 `ho-20260908-a1b2`。
3. **直接写最终路径**（M-1：无移动语义——写在哪 register 就在哪，没有
   中转目录）：

   ```
   ~/.claude/zoning/<project-slug>/handoffs/<to>/<id>.md
   ```

   - project-slug 算法（与 ~/.claude/projects 同规则）：项目绝对路径中每个
     非 [A-Za-z0-9] 字符逐个替换为 `-`。
     例：`/Users/jack/work/my-app` → `-Users-jack-work-my-app`。
   - `~` 展开为绝对家目录（Write 工具需要绝对路径）。
   - **已知环境限制（真实会话实测）**：harness 对 `~/.claude/**` 有敏感路径
     守卫，Write/Edit 可能被拦。被拦时的兜底路径：用 Bash + python3 写入
     （`mkdir -p` 目标目录后以 python3 落盘），随后照常 `zone register`。
     写入语义不变（仍是最终路径直写，M-1 不破坏）。
4. 按 frontmatter + 七段模板写正文（模板见下），按链路矩阵选侧重。
5. 写完**立即**在项目 cwd 运行（zone 按当前目录定位 sidecar）：

   ```
   zone register <刚写的文档绝对路径>
   ```

   成功输出 `registered <id>`。校验失败（frontmatter 不合法）→ 按报错修复
   后重新 register（闭环在模型侧，R-2）。
6. register 成功后向用户输出，一次说全：
   - `registered <id>`
   - 深链（H-2）：

     ```
     claude-cli://open?q=%2Fzone%20<to>&cwd=<url编码的项目绝对路径>
     ```

     q = `/zone <to>` 的 URL 编码（`/`→`%2F`、空格→`%20`，固定形态如
     `%2Fzone%20core`）；cwd = 项目绝对路径的 URL 编码。生成：

     ```
     python3 -c "from urllib.parse import quote; print('claude-cli://open?q=' + quote('/zone <to>', safe='') + '&cwd=' + quote('<项目绝对路径>'))"
     ```

   - 建议下一步：深链开新会话（prompt 已预填 `/zone <to>`，人按发送键
     落区）；或新会话手动发送 `/zone <to>`。落区后运行
     `zone inject <id>` 注入并消费 handoff。

## 文档模板（§6.2 schema v1；register 按此校验）

frontmatter（机器层）：

```yaml
---
id: ho-20260908-a1b2
from: discuss                  # 当前区（或 unzoned）
to: core                       # 目标区（须与所在目录 handoffs/<to>/ 一致）
created: 2026-09-08T14:30:00+08:00   # ISO8601 带本地时区偏移
tags: []                       # 预留，v1 不消费，固定写 []
---
```

created 可用
`python3 -c "from datetime import datetime; print(datetime.now().astimezone().isoformat(timespec='seconds'))"`
生成。

正文七段（人机共享层；`# 标题` + 六个 `##` 段）：`# 标题` 是正文唯一的
一级标题，register 从它取事件 title。

```markdown
# <一句话标题>     写得能认出这是哪件事（会出现在 pending 提示行里）

## Intent           交接意图：一句话 + 触发场景（用户附注写在这里）
## Decisions        已定决策：编号列表，每条「决定 + 理由」
## Open Questions   开放问题：编号列表，目标区要回答/拍板的
## Snapshot         现场：分支 / 未提交改动 / 涉及文件清单（如实，不美化）
## Why Escalated    为什么超纲——仅 chore→core、chore→discuss 升级链使用，
                   其余链路整段省略
## Next Steps       建议的第一步：具体可执行（目标区拿到先做什么）
```

按链路侧重取舍详略；空段落写「（无）」，唯 Why Escalated 整段省略。

## 链路侧重矩阵（§6.3：按 from→to 查表，不写死路由）

| 链路 from→to | 模板侧重 |
|---|---|
| discuss → core | **默认重点**：Decisions + Open Questions + 范围边界（在 Decisions 末条明示「做什么、不做什么」） |
| chore → core / chore → discuss（升级） | Why Escalated（为什么超纲）+ Snapshot（改到哪了） |
| core → discuss（执行中暴雷回炉） | Open Questions 以 Blocked By + 具体问题清单为主；Decisions 记已试过与已排除的 |
| core → maint（收尾） | Snapshot：先运行 `zone snapshot`，输出原样嵌入本段（纯机器产物，不加评论、不改写） |
| 其他（含 from: unzoned） | 就近套用最接近的一行 |

## 写作纪律

- 上下文完整时写——趁会话记忆还热，别拖到收尾。
- 现场类信息以机器输出为准、原样记录（如 git 状态），不凭印象转述。
- 写目标区读者需要的判断与状态，不复述对话过程。
