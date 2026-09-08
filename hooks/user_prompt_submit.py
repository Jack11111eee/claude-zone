#!/usr/bin/env python3
"""zoning UserPromptSubmit hook — thin wrapper (M-5; DESIGN.md §4/§9, A-2, M-3).

Matches ^/zone\\s+(chore|core|discuss|maint)$ → remedies the session into that
zone: `zone _zap-title` rewrites the title from the transcript's first user
message and appends a source:"command" index event, then the zone prompt (via
`zone _zone-prompt`) is injected as UserPromptSubmit additionalContext. stdout is
a single JSON line — the ready line is folded INTO additionalContext, never
printed bare. All other prompts (plain messages, `/zone` without args,
`/zone inject ho-xzy`) fall through silently — hooks don't scout normal chat.
"""
import json
import os
import re
import subprocess
import sys

ZONE_ARGS = {"chore", "core", "discuss", "maint"}
LABELS = {"chore": "杂活区", "core": "核心区", "discuss": "讨论区", "maint": "版本维护区"}
ZONE_RE = re.compile(r"^/zone\s+(\S+)$")


def run_zone(root, argv, stdin_text=None):
    proc = subprocess.run(
        ["python3", os.path.join(root, "bin", "zone"), *argv, "--json"],
        input=stdin_text, capture_output=True, text=True)
    return json.loads(proc.stdout)


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
    except (OSError, ValueError):
        return
    if not zone_prompt:
        return
    ctx = f"{LABELS[zone]}已就绪。\n{zone_prompt}"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": ctx,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
