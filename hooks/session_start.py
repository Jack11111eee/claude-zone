#!/usr/bin/env python3
"""zoning SessionStart hook — thin wrapper (M-5; DESIGN.md §3/§9, L-1).

Prefix parsing and index append live in `zone _register-session`; this hook only
filters (L-1 main-agent, startup-only), forwards the payload (event-level source
rewritten to "prefix" per §7.2), and renders the one-line zone-ready hint.
"""
import json
import os
import subprocess
import sys

LABELS = {"chore": "杂活区", "core": "核心区", "discuss": "讨论区", "maint": "版本维护区"}


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
        proc = subprocess.run(
            ["python3", os.path.join(root, "bin", "zone"), "_register-session", "--json"],
            input=json.dumps({**payload, "source": "prefix"}),
            capture_output=True, text=True)
        zone = json.loads(proc.stdout).get("data", {}).get("zone")
    except (OSError, ValueError):
        return  # never break session start — degrade to silent plain CC
    if zone in LABELS:  # unzoned → zero output (§3: silent plain CC)
        print(f"{LABELS[zone]}已就绪。")


if __name__ == "__main__":
    main()
