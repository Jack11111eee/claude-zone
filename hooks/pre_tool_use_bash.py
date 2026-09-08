#!/usr/bin/env python3
"""zoning PreToolUse (Bash) hook — thin wrapper (M-5; DESIGN.md §9, GUARD-02/04).

The guard evaluation (zone by sessionId from the index → merged definition's
bash_block_patterns regex blacklist, re.search per pattern on the command
string, §8.2 L-6) lives entirely in `zone _check-guard bash`; this hook only
forwards tool_input.command and session_id, then translates a deny into the
official PreToolUse decision JSON (permissionDecision/permissionDecisionReason
inside hookSpecificOutput). Missing command / zone bin failure → allow
(degrade-to-open: the guard deters, it never breaks the shell). allow →
silent exit 0.
"""
import json
import os
import subprocess
import sys


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    if not isinstance(payload, dict):
        return
    command = (payload.get("tool_input") or {}).get("command")
    if not command:
        return  # no command string → nothing to evaluate → allow
    session_id = payload.get("session_id") or ""
    cwd = payload.get("cwd")
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    argv = ["python3", os.path.join(root, "bin", "zone"),
            "_check-guard", "bash", f"--command={command}", "--json"]
    if session_id:
        argv.append(f"--session={session_id}")
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        verdict = json.loads(proc.stdout).get("data", {})
    except (OSError, ValueError):
        return  # bin missing / non-JSON → never block a command on guard failure
    if verdict.get("decision") != "deny":
        return
    reason = "维护区护栏：高危 git 操作需人工确认，请改用安全形态或换区执行。"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
