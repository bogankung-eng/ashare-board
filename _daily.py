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


def push_with_retry(url, branch="main", attempts=15, interval=60, timeout=60):
    """断网友好：每次 push 强制 timeout（避免无限挂起），失败后循环重试。

    根因修复：原 subprocess.run 无 timeout，github 不可达时 git 挂死、
    python 进程也随之永久阻塞在 subprocess 管道上（连续多日人工救场）。
    timeout 到期后子进程会被 kill，python 继续进入下一轮重试。"""
    for i in range(1, attempts + 1):
        try:
            r = subprocess.run(["git", "push", url, branch], cwd=BASE,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout)
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if out:
                print(out[-400:])
            if r.returncode == 0:
                print(f"OK push 成功（第 {i} 次）")
                return 0
            print(f"FAIL push（第 {i}/{attempts} 次）: {err[-200:]}")
        except subprocess.TimeoutExpired:
            print(f"FAIL push 超时（第 {i}/{attempts} 次，{timeout}s 无响应）")
        if i < attempts:
            print(f"  {interval}s 后重试...")
            time.sleep(interval)
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
    token = get_token()
    if not token:
        print("!!! 未找到 GitHub token（~/.git-credentials / CREDENTIALS.md）"); return 1
    url = REPO_URL.replace("https://", f"https://{token}@")
    if run(["git", "add", "-A"]) != 0:
        print("!!! git add 失败"); return 1
    run(["git", "commit", "-m", f"auto: 每日看板更新 {__import__('datetime').date.today()}"])
    push_rc = push_with_retry(url)
    if push_rc == 0:
        print("== 完成：线上看板 https://ashare-board.pages.dev/ 已更新 ==")
    else:
        print("!! 推送失败（已重试多轮），本地 commit 未丢失，可稍后手动 push")

    print("\n========== 收盘简报 ==========")
    run([PY, os.path.join(BASE, "_brief.py")])
    return 0 if push_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
