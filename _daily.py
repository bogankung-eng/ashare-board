#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股看板每日自动更新：采集 → 生成看板 → 更新部署物 → 推送 GitHub（CF 自动重新部署）
用法：python _daily.py
说明：非交易日 _collect 自动跳过；重复推送 up-to-date 无副作用
"""
import os
import re
import shutil
import subprocess
import sys
import json
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
REPO_URL = "https://github.com/bogankung-eng/ashare-board.git"


def run(cmd, cwd=BASE):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if out:
        print(out[-1200:])
    if err:
        print("STDERR:", err[-600:])
    return r.returncode


def get_token():
    """优先 ~/.git-credentials，兜底 CREDENTIALS.md"""
    cred = os.path.expanduser("~/.git-credentials")
    if os.path.exists(cred):
        m = re.search(r"https://(ghp_[^@\s]+)@", open(cred, encoding="utf-8").read())
        if m:
            return m.group(1)
    cfile = os.path.join(os.path.expanduser("~"), ".workbuddy", "CREDENTIALS.md")
    if os.path.exists(cfile):
        m = re.search(r"ghp_[A-Za-z0-9]+", open(cfile, encoding="utf-8").read())
        if m:
            return m.group(0)
    return None


def write_status(push_rc, attempts_used, note=""):
    """运行状态落盘：连续失败告警的判断依据（连续2天 push_rc!=0 时人工介入）。"""
    import datetime as _dt
    st = {"date": _dt.date.today().isoformat(),
          "time": _dt.datetime.now().strftime("%H:%M:%S"),
          "push_rc": push_rc, "push_attempts": attempts_used, "note": note}
    try:
        json.dump(st, open(os.path.join(BASE, "data", "_daily_status.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:
        print("WARN 状态文件写入失败:", e)


def push_with_retry(branch="main", attempts=3, timeout=60):
    """断网友好：每次 push 强制 timeout（避免无限挂起），指数退避重试。

    根因修复：原 subprocess.run 无 timeout，github 不可达时 git 挂死、
    python 进程也随之永久阻塞在 subprocess 管道上（连续多日人工救场）。
    timeout 到期后子进程会被 kill，python 继续进入下一轮重试。

    2026-09-26 二次修复：不再把 token 硬嵌 URL——token 失效时 GitHub 返回 401，
    git 会回退询问凭证助手，GCM 弹出「Connect to GitHub」登录窗打扰桌面用户。
    改为走 origin + GCM 凭证助手（gho_ OAuth 自动续期），并设
    GCM_INTERACTIVE=never / GIT_TERMINAL_PROMPT=0，凭证缺失时快速失败、绝不弹窗。

    2026-10-31 三次修复：原 15次×60s 最坏挂 15 分钟（10/27 实测 25m35s 全程
    黑箱）。改为 3 次×指数退避（30s/90s/240s），最坏 7 分钟内出结果。"""
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    backoffs = [30, 90, 240]
    for i in range(1, attempts + 1):
        try:
            r = subprocess.run(["git", "push", "origin", branch], cwd=BASE,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout, env=env)
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if out:
                print(out[-400:])
            if r.returncode == 0:
                print(f"OK push 成功（第 {i} 次）")
                write_status(0, i)
                return 0
            print(f"FAIL push（第 {i}/{attempts} 次）: {err[-200:]}")
        except subprocess.TimeoutExpired:
            print(f"FAIL push 超时（第 {i}/{attempts} 次，{timeout}s 无响应）")
        if i < attempts:
            wait = backoffs[min(i - 1, len(backoffs) - 1)]
            print(f"  {wait}s 后重试（指数退避）...")
            time.sleep(wait)
    write_status(1, attempts, "push 重试耗尽，本地 commit 未丢，可稍后手动 push")
    return 1


def main():
    print("== 1/4 采集盘后数据（非交易日自动跳过）==")
    rc = run([PY, os.path.join(BASE, "_collect.py")])
    if rc != 0:
        print("!!! 采集失败，中止"); return 1

    print("== 2/4 生成看板 ==")
    rc = run([PY, os.path.join(BASE, "_gen_board.py")])
    if rc != 0:
        print("!!! 生成失败，中止"); return 1

    print("== 3/4 更新部署物 public/index.html ==")
    os.makedirs(os.path.join(BASE, "public"), exist_ok=True)
    shutil.copy(os.path.join(BASE, "board.html"), os.path.join(BASE, "public", "index.html"))

    print("== 4/4 推送 GitHub（CF 自动重新部署）==")
    if run(["git", "add", "-A"]) != 0:
        print("!!! git add 失败"); return 1
    run(["git", "commit", "-m", f"auto: 每日看板更新 {__import__('datetime').date.today()}"])
    push_rc = push_with_retry()
    if push_rc == 0:
        print("== 完成：线上看板 https://ashare-board.pages.dev/ 已更新 ==")
    else:
        print("!! 推送失败（已重试多轮），本地 commit 未丢失，可稍后手动 push")

    print("\n========== 收盘简报 ==========")
    run([PY, os.path.join(BASE, "_brief.py")])
    return 0 if push_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
