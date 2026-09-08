#!/usr/bin/env python3
"""zoning PreToolUse (Write|Edit) hook — thin wrapper (M-5; DESIGN.md §9, GUARD-01/03).

The guard evaluation (zone by sessionId from the index → merged definition's
deny_write_edit → allow_paths glob carve-out) lives entirely in
`zone _check-guard write`; this hook only forwards tool_input.file_path and
session_id, then translates a deny into the official PreToolUse decision JSON
(permissionDecision/permissionDecisionReason inside hookSpecificOutput).
Missing path / zone bin failure → allow (degrade-to-open: the guard must never
break writes, it only deters zoned sessions from editing source). allow →
silent exit 0. Deny-reason wording is single-sourced from zones/*.yaml
`display` (07-01) via `zone _check-guard`'s display field — this hook only
appends the 区 suffix, falling back to the raw zone name when display is
absent (degrade-to-open spirit: wording must not create a failure path).
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
    path = (payload.get("tool_input") or {}).get("file_path")
    if not path:
        return  # no target path → nothing to evaluate → allow
    session_id = payload.get("session_id") or ""
    cwd = payload.get("cwd")
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    argv = ["python3", os.path.join(root, "bin", "zone"),
            "_check-guard", "write", f"--path={path}", "--json"]
    if session_id:
        argv.append(f"--session={session_id}")
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        verdict = json.loads(proc.stdout).get("data", {})
    except (OSError, ValueError):
        return  # bin missing / non-JSON → never block a write on guard failure
    if verdict.get("decision") != "deny":
        return
    zone = verdict.get("zone")
    label = f"{verdict.get('display') or zone}区"
    reason = f"{label}护栏：本区禁止修改源码。请用 /handoff 交接或 /zone 换区。写 handoff 文档不受限。"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
