#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股行情看板生成器（P11b 起为薄入口，实体在 boardlib/）
用法：
    python _gen_board.py                # 渲染所有已采集日期
    python _gen_board.py --date=20260818  # 只渲染指定日期
输出：board.html
"""
import argparse
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from boardlib.analysis import build, load_dates, write_history
from boardlib.config import BASE, DB, OUT
from boardlib.template import TEMPLATE


def main():
    ap = argparse.ArgumentParser(description="P1 短线看板生成器")
    ap.add_argument("--date", default=None, help="只渲染指定日期 YYYYMMDD")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    dates = load_dates(conn)
    conn.close()
    if args.date:
        if args.date not in dates:
            print(f"[错误] {args.date} 无数据，可选: {dates}")
            return
        dates = [args.date]

    data = write_history(build(dates))
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    # 供应链安全：gsap 内联（CDN 被墙时页面动画失效/白屏风险），本地 assets 优先，缺失时回退 CDN
    gsap_path = os.path.join(BASE, "assets", "gsap.min.js")
    if os.path.exists(gsap_path):
        gsap_src = "<script>" + open(gsap_path, encoding="utf-8").read() + "</script>"
    else:
        gsap_src = '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>'
        print("[WARN] assets/gsap.min.js 缺失，回退 CDN")
    html = html.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>', gsap_src)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 看板已生成 -> {OUT}（{len(dates)} 个交易日: {dates}）")


if __name__ == "__main__":
    main()
