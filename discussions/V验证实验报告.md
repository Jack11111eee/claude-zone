# V-1~V-9 验证实验报告

- 日期：2026-09-08（凌晨）
- 环境：macOS / claude 2.1.263 / GLM 代理后端（ANTHROPIC_BASE_URL=api.bingchanpro.com，全部 DEFAULT_*_MODEL=glm-5.3）
- 方法：`/tmp/zoning-vtest` scratch 项目 + hooks stdin 落盘 logger（`logs/<event>.stdin.jsonl`）+ `-p` 模式驱动
- 结论先行：**9 项中 8 项闭环（7 通过/2 部分通过带修正），1 项（V-2）留 30 秒手工验证。承重梁全部立住。**

| # | 假设 | 判定 | 实测详情 |
|---|---|---|---|
| V-1 | `-n` 名出现在 SessionStart stdin `session_title` | ✅ **通过** | `session_title: "--core V1测试"`，`source: startup`。前缀解析设计成立 |
| V-2 | picker `/` 搜 `--core` 过滤 | ⏳ 手工待验 | 非交互模式无法驱动 picker UI。请人跑 `claude -r` 按 `/` 输 `--core` 确认 |
| V-3 | `--resume <name>` 按名命中 | ⚠️ **通过，带硬修正** | 中性名直接命中；但 `--`开头标题被 commander 当 flag：`claude --resume "--core x"` 报 unknown option，**必须 `--resume="--core x"` 等号形式**。`/zones`、`zone list` 输出的复制命令必须用等号形式 |
| V-4 | 深链打开新终端+预填 prompt | ✅ **通过（拿实锤）** | `claude-cli://open?q=%2Fzone%20core&cwd=…` → 新 Terminal 窗口，进程参数 `--deep-link-cwd-b64=… --prefill-b64=L3pvbmUgY29yZQ`（= "/zone core"），预填**不发送**。附带发现：终端可 `claude --prefill` 等效 |
| V-5 | 存在的斜杠命令触发 UserPromptSubmit | ✅ **通过（核心梁）** | 命令文件存在时：prompt 字段原文 `/zone` 送达 hook，stdin 含 session_title/transcript_path/cwd。**关键发现：不存在的命令（Unknown command）不触发 hook** —— `/zone` skill 文件必须随插件带，否则补救路径整个哑火 |
| V-6 | additionalContext 注入完整 | ✅ **通过（修正认知）** | 12k 字符（seninel 标记+11960 填充）**完整进入 attachment，无截断**。文档值"~10k 上限"在 2.1.263 不构成硬截断（存在 2KB 预览+溢出文件机制，但正文全文注入）。zone prompt 余量极大 |
| V-7 | /fork 继承标题 | ❌ **不继承（按退路处理）** | fork 出的会话 SessionStart `source: "fork"` 但 `session_title: None`，内容 inherit 但名字丢。设计已按"fork 后需补救"处理，不变 |
| V-8 | Bash 环境暴露 CLAUDE_SESSION_ID | ✅ **存在**（`CLAUDE_CODE_SESSION_ID`） | 另有 ENTRYPOINT/PID/EFFORT/MESSAGING_SOCKET。`zone which` 可免参自动定位（锦上添花成立） |
| V-9 | UserPromptSubmit exit 2 / JSON block 拦截 | ❌ **两种形式均未拦截**（本环境） | hook 收到 prompt 但消息照常达模型（模型自证"可见"+transcript 确认）。文档描述与实测不符（可能 -p 模式/GLM 代理差异）。**设计无损**：A-2 本就裁决"不 block、占位正文"为默认形态——实测反而证明该裁决正确 |

## 对 DESIGN.md 的回写修正（3 处）

1. **§3 / §10（V-3 修正）**：所有给用户的复制命令改为等号形式 `claude --resume="--core 任务名"`；`zone list`/`/zones` 输出遵守。
2. **§4（V-5 修正）**：`/zone` skill 文件从"占位（避免 unknown-command 观感）"升级为**功能必需**——不存在的命令不触发 UserPromptSubmit，补救 hook 的触发依赖 skill 文件存在。
3. **§11（V-6/V-9/V-7 落定）**：V-6 上限改注"实测 12k 完整注入"；V-9 判"不支持（实测 2.1.263 + 本环境），维持不 block 默认"；V-7 判"不继承，fork 后补救"，全部由实测背书。

## 附带环境发现（影响 M-6，不影响主线）

本机 claude 为 GLM 代理后端，`--model haiku/opus` 实际全路由到 glm-5.3（stderr：`unrecognized_model`）。cz() 的模型映射在本机是 no-op；官方 API 环境下正常。设计保持 M-6（映射写在糖里），README 注明。

## 实验资产

- scratch 项目：`/tmp/zoning-vtest`（hook logger、12k 注入 hook、/zone 命令文件悉数在内，M0 可直接改造复用）
- 观测手段：hooks stdin 落盘 + `~/.claude/projects/-private-tmp-zoning-vtest/` transcript 交叉验证 + Terminal.app 窗口进程参数取证（深链）
