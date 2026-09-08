# 延迟等级与 hook 超时预算

zoning 的 hooks 会话每次启动都跑。Claude Code hook 超时默认 60s（SessionStart 系统级上限），plugin hooks 默认曾有更紧档位。设计要求 hook 是薄封装（M-5：逻辑在 bin），每次执行 = 一次 python3 启动 + 一次 zone 子命令。实测（本 repo，M1 开发中）：

- `python3 bin/zone which --session x`（含 python3 解释器启动）：~140ms
- `_register-session`（stdin 解析 + append）：~145ms

结论：五个 hook 全开的最坏路径（SessionStart 里 _register-session + pending 探测两次子进程）≈ 400ms，远低于超时。无需异步/常驻——常驻进程违反"无 daemon"理念（§1 第 3 条）。

——本文档供 01-02/02-02 hook 实现与后续性能验收参照。
