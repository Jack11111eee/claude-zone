#!/usr/bin/env python3
"""zoning UserPromptSubmit hook — thin wrapper (M-5; DESIGN.md §4/§9, A-2, M-3).

Matches ^/zone\\s+(chore|core|discuss|maint)$ → remedies the session into that
zone: `zone _zap-title` rewrites the title from the transcript's first user
message and appends a source:"command" index event, then the zone prompt (via
`zone _zone-prompt`) is injected as UserPromptSubmit additionalContext. After
the switch it probes unconsumed handoffs (§6.5, M-3: same caliber as
SessionStart) via `zone pending` — the hook never scans directories itself.
stdout is a single JSON line — the ready line is folded INTO additionalContext,
never printed bare. All other prompts (plain messages, `/zone` without args,
`/zone inject ho-xzy`) fall through silently — hooks don't scout normal chat.
Ready-line wording is single-sourced from zones/*.yaml `display` (07-01):
the same `zone _zone-prompt` response carries it next to the prompt — this
hook only appends the 区 suffix, never maps zone→label itself.
"""
import json
import os
import re
import subprocess
import sys

ZONE_ARGS = {"chore", "core", "discuss", "maint"}
ZONE_RE = re.compile(r"^/zone\s+(\S+)$")


def run_zone(root, argv, stdin_text=None):
    proc = subprocess.run(
        ["python3", os.path.join(root, "bin", "zone"), *argv, "--json"],
        input=stdin_text, capture_output=True, text=True)
    return json.loads(proc.stdout)


def probe_pending(root, zone, cwd):
    """未消费 handoff 探测（§6.5；M-3 与 SessionStart 同口径）——逻辑
    全部在 `zone pending`（03-02 双源真值），hook 只转发子命令调用（以会话
    项目 cwd 定位 sidecar）。失败静默：提示段缺席不影响注入。"""
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
        return
    if not isinstance(payload, dict):
        return
    prompt = payload.get("prompt") or ""
    m = ZONE_RE.match(prompt)
    if not m or m.group(1) not in ZONE_ARGS:  # no scout: silent for everything else
        return
    zone = m.group(1)
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    try:
        zt = run_zone(root, ["_zap-title"], json.dumps({**payload, "zone": zone}))
        zp = run_zone(root, ["_zone-prompt", zone])
        if not zt.get("ok") or not zp.get("ok"):
            return  # bad transcript paths degrade silently — zone title/gen unzoned stays plain CC
        zone_prompt = zp.get("data", {}).get("prompt")
        display = zp.get("data", {}).get("display")
    except (OSError, ValueError):
        return
    if not zone_prompt or not display:
        return
    # Pending probe lives in `zone pending` (M-3/M-5); hook only formats the hint
    hint = format_pending_hint(probe_pending(root, zone, payload.get("cwd")))
    ctx = f"{display}区已就绪。\n{zone_prompt}" + (f"\n{hint}" if hint else "")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": ctx,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
