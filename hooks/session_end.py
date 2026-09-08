#!/usr/bin/env python3
"""zoning SessionEnd hook — thin wrapper (M-5; DESIGN.md §3/§9, SESS-01/02).

lastSeen logic lives in `zone _touch` (判区 by sessionId → lastSeen 事件
append)；this hook only forwards the payload (event-level source is set to
"session_end" by the bin). Failure of any kind stays silent exit 0 — SessionEnd
must never block or error the session teardown. stdout stays empty: no output
for zoned or unzoned sessions alike（SESS-02 零打扰）.
"""
import json
import os
import subprocess
import sys


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    try:
        subprocess.run(
            ["python3", os.path.join(root, "bin", "zone"), "_touch", "--json"],
            input=json.dumps(payload), capture_output=True, text=True)
    except OSError:
        pass  # never break session end — degrade to silent plain CC


if __name__ == "__main__":
    main()
