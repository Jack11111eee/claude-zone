#!/usr/bin/env python3
"""Phase 9 09-01: maint Bash 护栏矩阵测试（GUARD-05/06，ZONING_HOME 隔离）。

纯标准库。直接 `python3 tests/test_guard_hardening.py` 重跑；断言用
print PASS/FAIL，任一 FAIL → exit 1，全 PASS → exit 0。

三组：
  A 新拦截组  —— 09-01 修的绕过面（-Xfd/-xfd/-Xf/-fx/双空格全家）
  B 回归组    —— v1.0 十用例矩阵全量复测（force-with-lease 放行锚点在内）
  C 边界组    —— `git clone -Xfd`（clean 前有他词）不拦；
                  `echo git clean -f`（re.search 子串语义）→ 如实断言 deny。

链路：subprocess 调真 bin/zone（插件根相对本文件），seed session 走
`_register-session`（stdin JSON，同真 hook），裁决走 `_check-guard bash`
（判区 by sessionId → 合并定义 bash_block_patterns 逐条 re.search）。
隔离：测试工作目录与 ZONING_HOME 均在 tempfile.mkdtemp 下，用后即清。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
ZONE_BIN = os.path.join(PLUGIN_ROOT, "bin", "zone")

# ---------------------------------------------------------------------------
# 用例矩阵
# ---------------------------------------------------------------------------

# A 新拦截组：plan 实测缺口 + 组合旗标族（每条一个用例）
NEW_DENY = [
    ("A1 git clean -Xfd（X 在 f 前的组合旗标）", "git clean -Xfd"),
    ("A2 git clean -xfd（f 在前的小写组合）", "git clean -xfd"),
    ("A3 git clean -Xf（X+f 二字符组合）", "git clean -Xf"),
    ("A4 git clean -fx（f+x 二字符组合）", "git clean -fx"),
    ("A5 git  clean -Xfd（git 与 clean 间双空格）", "git  clean -Xfd"),
    ("A6 git  clean -Xf（双空格 × 组合旗标交叉）", "git  clean -Xf"),
    ("A7 git  push origin main --force（push 双空格面）", "git  push origin main --force"),
]

# B 回归组：v1.0 十用例矩阵（04-02-PLAN verify 条目全量）
#   7 deny + force-with-lease allow + status allow + core 会话不拦
REGRESSION_DENY = [
    ("B1 git push --force origin main", "git push --force origin main"),
    ("B2 git reset --hard HEAD~3", "git reset --hard HEAD~3"),
    ("B3 git branch -D feature/x", "git branch -D feature/x"),
    ("B4 git clean -f", "git clean -f"),
    ("B5 git checkout main -- src/x.py", "git checkout main -- src/x.py"),
    ("B6 git reflog expire --expire=now --all",
     "git reflog expire --expire=now --all"),
    ("B7 git gc --prune=now", "git gc --prune=now"),
]
REGRESSION_ALLOW = [
    ("B8 git push --force-with-lease origin main（GUARD-04 回归锚点）",
     "git push --force-with-lease origin main"),
    ("B9 git status", "git status"),
    ("B10 git clean -n（干跑不受收紧误伤）", "git clean -n"),
]

# C 边界组：clean 二字锚定；re.search 子串语义如实断言
BOUNDARY = [
    ("C1 git clone -Xfd 不拦（clone 不是 clean）",
     "git clone -Xfd", "allow"),
    ("C2 echo git clean -f —— re.search 子串命中为 deny（现有语义，如实断言）",
     "echo git clean -f", "deny"),
]

# ---------------------------------------------------------------------------
# 隔离环境 + bin 封装
# ---------------------------------------------------------------------------

class Sandbox:
    """ZONING_HOME + 工作 cwd 隔离：seed 会话、跑裁决、催 data dict。"""

    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="gdh-")
        # realpath：macOS $TMPDIR 是符号链接（/var → /private/var），子进程
        # os.getcwd() 返回解析后路径——seed 与 guard 的 slug 必须同串。
        self.cwd = os.path.realpath(os.path.join(self.base, "work"))
        os.makedirs(self.cwd)
        self.env = dict(os.environ, ZONING_HOME=os.path.join(self.base, "zhome"))

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def _run(self, argv, stdin_text=None):
        proc = subprocess.run(
            [sys.executable, ZONE_BIN, *argv, "--json"],
            input=stdin_text, capture_output=True, text=True,
            cwd=self.cwd, env=self.env)
        return proc

    def seed_session(self, session_id, title):
        payload = json.dumps({
            "session_id": session_id,
            "session_title": title,
            "cwd": self.cwd, "source": "startup"})
        proc = self._run(["_register-session"], stdin_text=payload)
        return json.loads(proc.stdout)

    def check_bash(self, command, session_id):
        proc = self._run(
            ["_check-guard", "bash", f"--command={command}",
             f"--session={session_id}"])
        return json.loads(proc.stdout).get("data", {})


# ---------------------------------------------------------------------------
# 断言与主流程
# ---------------------------------------------------------------------------

PASS_N = FAIL_N = 0


def report(ok, name, detail=""):
    global PASS_N, FAIL_N
    if ok:
        PASS_N += 1
        print(f"PASS {name}")
    else:
        FAIL_N += 1
        print(f"FAIL {name} {detail}", file=sys.stderr)


def expect_denied(box, name, command, session_id="s-maint"):
    data = box.check_bash(command, session_id)
    decide = data.get("decision") == "deny" and data.get("zone") == "maint"
    echo = isinstance(data.get("pattern"), str) and data["pattern"]
    report(decide and echo, name,
           f"→ {data.get('decision')}/{data.get('zone')}(want deny/maint) "
           f"pattern={data.get('pattern')!r}")


def expect_allowed(box, name, command, session_id="s-maint"):
    data = box.check_bash(command, session_id)
    report(data.get("decision") == "allow", name,
           f"→ {data.get('decision')}/{data.get('zone')}(want allow)")


def main():
    box = Sandbox()
    try:
        # seed：maint（黑名单主体）与 core（非 maint 不拦对照）各一会话
        r_maint = box.seed_session("s-maint", "--maint guard matrix")
        r_core = box.seed_session("s-core", "--core guard matrix")
        report(r_maint.get("data", {}).get("zone") == "maint"
               and r_core.get("data", {}).get("zone") == "core",
               "seed 两会话（maint/core）落地 sidecar",
               f"→ {r_maint} {r_core}")

        # 非 maint 会话不查黑名单（v1.0 十用例的第 10 条）
        expect_allowed(box, "B0 core 会话 git push --force 不拦（非 maint）",
                       "git push --force origin main", session_id="s-core")

        # 无会话 id → unzoned 放行（GUARD-03 degrade-to-open）
        data = box.check_bash("git clean -Xfd", "")
        report(data.get("decision") == "allow" and data.get("zone") == "unzoned",
               "U1 未登记会话（伪造 sid）unzoned 放行",
               f"→ {data.get('decision')}/{data.get('zone')}")

        for name, command in NEW_DENY:
            expect_denied(box, name, command)
        for name, command in REGRESSION_DENY:
            expect_denied(box, name, command)
        for name, command in REGRESSION_ALLOW:
            expect_allowed(box, name, command)
        for name, command, expected in BOUNDARY:
            fn = expect_denied if expected == "deny" else expect_allowed
            fn(box, name, command)

        # yaml 解析管线吃新正则：show maint（受限解析器 + 重渲染）
        proc = box._run(["show", "maint"])
        ok = proc.returncode == 0
        shown = ""
        if ok:
            shown = json.loads(proc.stdout).get("data", {}).get("zone_yaml", "")
        report(ok and "git\\s+clean\\s+.*-[a-zA-Z]*f" in shown,
               "S1 zone show maint 跑通且含新 clean 正则",
               f"→ exit={proc.returncode} "
               f"hit={'git\\\\s+clean\\\\s+.*-[a-zA-Z]*f' if ok else False}")

        # doctor 一并确认内置定义仍合法（七条新正则全部可编译）
        proc = box._run(["doctor"])
        report(proc.returncode == 0, "S2 zone doctor 通过（新正则定义合法）",
               f"→ exit={proc.returncode} {proc.stdout[:200]}")
    finally:
        box.close()

    print(f"--- {PASS_N} passed, {FAIL_N} failed ---")
    return 1 if FAIL_N else 0


if __name__ == "__main__":
    sys.exit(main())
