#!/usr/bin/env python3
"""zoning SessionStart hook — thin wrapper (M-5; DESIGN.md §3/§9, L-1).

Prefix parsing and index append live in `zone _register-session`; this hook only
filters (L-1 main-agent, startup-only), forwards the payload (event-level source
rewritten to "prefix" per §7.2), injects the zone prompt (via `zone
_zone-prompt`) as SessionStart additionalContext, and probes unconsumed
handoffs (§6.5) via `zone pending` (M-3/03-02: dual-source truth, hook never
scans directories itself). stdout must be a single JSON line — the
human-readable ready line is folded INTO additionalContext's leading line (any
bare line before the JSON breaks Claude's stdout-as-JSON parsing).
unzoned sessions stay zero-output (§3: silent plain CC).
"""
import json
import os
import subprocess
import sys

LABELS = {"chore": "杂活区", "core": "核心区", "discuss": "讨论区", "maint": "版本维护区"}


def run_zone(root, argv, stdin_text=None):
    proc = subprocess.run(
        ["python3", os.path.join(root, "bin", "zone"), *argv, "--json"],
        input=stdin_text, capture_output=True, text=True)
    return json.loads(proc.stdout)


def probe_pending(root, zone, cwd):
    """未消费 handoff 探测（§3/§6.5）——逻辑全部在 `zone pending`（03-02
    双源真值），hook 只转发子命令调用（以会话项目 cwd 定位 sidecar）。
    失败静默：提示段缺席不影响注入。"""
    try:
        proc = subprocess.run(
            ["python3", os.path.join(root, "bin", "zone"),
             "pending", f"--zone={zone}", "--json"],
            cwd=cwd, capture_output=True, text=True)
        return json.loads(proc.stdout).get("data", {}).get("items") or []
    except (OSError, ValueError):
        return []


def format_pending_hint(items):
    """提示≠注入（D-002）：只列出存在与消费入口，全文须经用户确认 inject。
    数字序号、每行一条、上限 5 条，超出以「等 N 条」收口。空列表 → 空串。
    """
    if not items:
        return ""
    lines = ["未消费 handoff："]
    for no, item in enumerate(items[:5], 1):
        hid = item.get("id") or "?"
        title = item.get("title") or hid
        lines.append(f"{no}) {title} → /zone inject {hid}")
    if len(items) > 5:
        lines.append(f"…等 {len(items)} 条")
    return "\n".join(lines)



def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    if payload.get("agent_type"):  # L-1: subagent/skill context, not a main session
        return
    if payload.get("source") != "startup":  # resume/clear/compact: M2 hangs pending probe here
        return
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    try:
        data = run_zone(root, ["_register-session"],
                        json.dumps({**payload, "source": "prefix"})).get("data", {})
        zone = data.get("zone")
        if zone not in LABELS:  # unzoned → zero output (§3: silent plain CC)
            return
        prompt = run_zone(root, ["_zone-prompt", zone]).get("data", {}).get("prompt")
    except (OSError, ValueError):
        return  # never break session start — degrade to silent plain CC
    if not prompt:
        return
    # Pending probe lives in `zone pending` (M-3/M-5); hook only formats the hint
    hint = format_pending_hint(probe_pending(root, zone, payload.get("cwd")))
    # Ready-line rides INSIDE additionalContext (stdout must stay pure one-line JSON)
    ctx = f"{LABELS[zone]}已就绪。\n{prompt}" + (f"\n{hint}" if hint else "")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": ctx,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
