#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite 数据治理：原始行按月归档出库 + 主库 VACUUM。

背景：board.db 两个月 93MB——pool_daily（全字段 data_json）与 news（快讯原文）
无限累积，查询与备份随时间退化。

策略：
  - >ARCHIVE_DAYS 天的 pool_daily / news / collect_log 行移入
    data/archive/archive_YYYYMM.db（按年月分文件，ATTACH 可查、历史可回）
  - 主库 VACUUM 回收空间
  - 历史日切换窗口（board.html 最近 ~60 交易日 < 90 天）不受影响
用法：
  python _archive.py            # 归档 + VACUUM
  python _archive.py --dry      # 只统计不动作
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "board.db")
ARCHIVE_DAYS = 90
TABLES = [  # (表名, 日期表达式, 日期格式)——比较格式必须与列内格式一致，
          # 否则 '2026-09-06' < '20260802' 恒真（'-'<'0'）会误归档整表
          ("pool_daily", "date", "%Y%m%d"),
          ("news", "substr(pub_time,1,10)", "%Y-%m-%d"),
          ("collect_log", "date", "%Y%m%d")]


def month_db(date_str):
    """date_str(YYYYMMDD 或 YYYY-MM-DD...) → data/archive/archive_YYYYMM.db"""
    ym = "".join(ch for ch in str(date_str)[:7] if ch.isdigit())[:6]
    adir = os.path.join(BASE, "data", "archive")
    os.makedirs(adir, exist_ok=True)
    return os.path.join(adir, f"archive_{ym}.db")


def count_old(conn, expr, cutoff):
    return conn.execute(f"SELECT COUNT(*) FROM {expr[0]} WHERE {expr[1]} < ?",
                        (cutoff,)).fetchone()[0]


def archive_table(conn, expr, cutoff, dry):
    name, dexpr, _fmt = expr
    rows = conn.execute(f"SELECT {dexpr}, COUNT(*) FROM {name} "
                        f"WHERE {dexpr} < ? GROUP BY {dexpr}", (cutoff,)).fetchall()
    if not rows:
        return 0
    moved = 0
    for date_val, n in rows:
        adb = month_db(date_val)
        if dry:
            print(f"  [dry] {name} {date_val}: {n} 行 → {os.path.basename(adb)}")
            moved += n
            continue
        arch = sqlite3.connect(adb)
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({name})")]
        arch.execute(f"CREATE TABLE IF NOT EXISTS {name} ({','.join(cols)})")
        ph = ",".join("?" * len(cols))
        data = conn.execute(f"SELECT {','.join(cols)} FROM {name} WHERE {dexpr} = ?",
                            (date_val,)).fetchall()
        arch.executemany(f"INSERT OR IGNORE INTO {name} VALUES ({ph})", data)
        arch.commit()
        arch.close()
        conn.execute(f"DELETE FROM {name} WHERE {dexpr} = ?", (date_val,))
        moved += n
    return moved


def main():
    dry = "--dry" in sys.argv
    conn = sqlite3.connect(DB)
    cutoff = (datetime.now() - timedelta(days=ARCHIVE_DAYS)).strftime("%Y%m%d")
    print(f"归档阈值：{ARCHIVE_DAYS} 天前（< {cutoff}）")
    total = 0
    for expr in TABLES:
        cutoff_fmt = (datetime.now() - timedelta(days=ARCHIVE_DAYS)).strftime(expr[2])
        old = count_old(conn, expr, cutoff_fmt)
        if old:
            print(f"{expr[0]}: {old} 行超龄（< {cutoff_fmt}）")
            total += archive_table(conn, expr, cutoff_fmt, dry)
        else:
            print(f"{expr[0]}: 无超龄行")
    if dry:
        print(f"[dry] 合计将归档 {total} 行，不执行动作")
        return 0
    conn.commit()
    print("VACUUM 主库...", )
    conn.execute("VACUUM")
    size = os.path.getsize(DB) / 1048576
    print(f"完成：归档 {total} 行，主库现 {size:.1f} MB")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
