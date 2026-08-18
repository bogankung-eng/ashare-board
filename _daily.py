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


def main():
    print("== 1/4 采集盘后数据（非交易日自动跳过）==")
    rc = run([PY, os.path.join(BASE, "_collect.py")])
    if rc != 0:
        print("!!! 采集失败，中止"); return 1

    print("== 2/4 生成看板 ==")
    rc = run([PY, os.path.join(BASE, "_gen_board.py")])
    if rc != 0:
        print("!!! 生成失败，中止"); return 1

    print("== 3/4 更新部署物 index.html ==")
    shutil.copy(os.path.join(BASE, "board.html"), os.path.join(BASE, "index.html"))

    print("== 4/4 推送 GitHub（CF 自动重新部署）==")
    token = get_token()
    if not token:
        print("!!! 未找到 GitHub token（~/.git-credentials / CREDENTIALS.md）"); return 1
    url = REPO_URL.replace("https://", f"https://{token}@")
    if run(["git", "add", "-A"]) != 0:
        print("!!! git add 失败"); return 1
    run(["git", "commit", "-m", f"auto: 每日看板更新 {__import__('datetime').date.today()}"])
    rc = run(["git", "push", url, "main"])
    if rc != 0:
        print("!!! 推送失败"); return 1

    print("== 完成：线上看板 https://ashare-board.bogan-kung.workers.dev/ 已更新 ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
