#!/usr/bin/env python3
"""zoning SessionStart hook — thin wrapper (M-5; DESIGN.md §3/§9, L-1).

Prefix parsing and index append live in `zone _register-session`; this hook only
filters (L-1 main-agent, startup-only), forwards the payload (event-level source
rewritten to "prefix" per §7.2), and injects the zone prompt (via `zone
_zone-prompt`) as SessionStart additionalContext. stdout must be a single JSON
line — the human-readable ready line is folded INTO additionalContext's leading
line (any bare line before the JSON breaks Claude's stdout-as-JSON parsing).
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
    # Ready-line rides INSIDE additionalContext (stdout must stay pure one-line JSON)
    ctx = f"{LABELS[zone]}已就绪。\n{prompt}"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": ctx,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
