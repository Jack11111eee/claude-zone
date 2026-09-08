---
name: zones
---

巡视当前项目的全部分区状态（只读命令——不写任何文件、不 append 任何事件）。

## 执行步骤

1. 运行 `zone list --json` 与 `zone pending --json`（在项目 cwd）。
2. 按区分组渲染总览（chore/core/discuss/maint 四组；未登记的会话归「unzoned」
   组不显示，保持零打扰哲学）：

   ```
   核心区（core）
     最近会话：
       --core 订单实施            2小时前
     未消费 handoff：
       ho-20260908-0132  订单表事件溯源重做…   discuss→core   1小时前
   ```

   - 会话行：title 截 40 字 + 相对时间。
   - handoff 行：id、标题截 40 字、from→to、相对时间。孤儿如实标 (unregistered)。
   - 空区显示（无会话且无 handoff）即可省略整组。

3. 尾部给"继续工作"的复制命令样本（**一律等号形式**，V-3 实测：空格形式
   `--resume "--core x"` 会被 CLI 当未知 flag 报错）：

   ```
   claude --resume="--core 订单实施"
   ```

   按每个会话行生成对应命令。**加粗警告格式**提醒：务必等号形式。

4. 如需开新终端预填落区命令，给深链（H-2 修订版）：

   ```
   claude-cli://open?q=%2Fzone%20core&cwd=<url编码的项目绝对路径>
   ```

## 纪律

- 只读：本命令不写文件、不改标题、不 append 事件——与 D-002 一致
  （模型可建议，永不代办；巡视是看，不是动）。
- 未消费 handoff 的消费流程（inject）由用户在目标区会话里自行发起，
  这里只列出与指引，不执行。
