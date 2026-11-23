# -*- coding: utf-8 -*-
"""P23 技术形态识别单测：合成 K 线正反例。

合成口径：
- 涨停判定完全由 pool_daily 提供（连板数直接写入 data_json），
  不依赖涨幅阈值，测试只验证 patterns 自身的状态机。
- P1 回调带 = 首板开盘价 ×[0.97, 1.02]；P2 振幅阈值 8%；P3 触 MA10 ±2%。
"""
import json
import sqlite3

import pytest

from boardlib import patterns

DATES = ["202601%02d" % i for i in range(1, 15)]  # 14 个交易日


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kline(code TEXT, date TEXT, open REAL, high REAL, low REAL, "
                 "close REAL, volume REAL, amount REAL, pct REAL)")
    conn.execute("CREATE TABLE pool_daily(date TEXT, pool_type TEXT, code TEXT, name TEXT, "
                 "data_json TEXT, collected_at TEXT)")
    return conn


def put_k(conn, code, rows):
    conn.executemany("INSERT INTO kline VALUES(?,?,?,?,?,?,0,0,0)",
                     [(code, d, o, h, l, c) for d, o, h, l, c in rows])


def put_zt(conn, date, code, lbv, name):
    conn.execute("INSERT INTO pool_daily VALUES(?,'zt',?,?,?,'')",
                 (date, code, name, json.dumps({"连板数": lbv})))


def flat(conn, code, n=10, px=11.0):
    """n 根横盘 K 线打底（给 MA10 预热）"""
    put_k(conn, code, [(DATES[i], px, px + 0.05, px - 0.05, px) for i in range(n)])


def test_p1_refirst_fired_and_band():
    """P1：低点入带 + 再次涨停 → fired；低点破带过深 → 不触发。"""
    conn = make_conn()
    # A 正例：D1 首板 o=10 → D2 低点 10.05（带内）→ D3 再板
    put_k(conn, "000001", [
        (DATES[0], 10.0, 11.0, 9.9, 11.0),
        (DATES[1], 10.8, 10.9, 10.05, 10.3),
        (DATES[2], 10.3, 11.33, 10.25, 11.33),
    ])
    put_zt(conn, DATES[0], "000001", 1, "甲")
    put_zt(conn, DATES[2], "000001", 1, "甲")
    # B 反例：低点 8.9（首板开盘价 -11%，带外）→ 即使 D3 再板也不触发
    put_k(conn, "000002", [
        (DATES[0], 10.0, 11.0, 9.9, 11.0),
        (DATES[1], 10.5, 10.6, 8.9, 9.2),
        (DATES[2], 9.3, 10.12, 9.2, 10.12),
    ])
    put_zt(conn, DATES[0], "000002", 1, "乙")
    put_zt(conn, DATES[2], "000002", 1, "乙")
    res = patterns.detect(conn, DATES)
    f = res["fired"]["refirst"]
    assert [e["code"] for e in f] == ["000001"]
    assert f[0]["date"] == DATES[2] and f[0]["meta"]["gap"] == 2
    assert -1.0 <= f[0]["meta"]["dip"] <= 2.0
    assert all(e["code"] != "000002" for e in f)


def test_p1_watching():
    """P1：首板后入带但尚未再板 → watching（且首板必须仍在 5 天窗口内）。"""
    conn = make_conn()
    flat(conn, "000003", 9, 5.0)
    put_k(conn, "000003", [
        (DATES[9], 5.0, 5.5, 4.95, 5.5),    # D10 首板
        (DATES[10], 5.3, 5.35, 5.05, 5.1),  # D11 低点入带
        (DATES[11], 5.1, 5.25, 5.15, 5.2),
        (DATES[12], 5.2, 5.25, 5.10, 5.15),
        (DATES[13], 5.15, 5.2, 5.14, 5.18),  # 至今日未再板
    ])
    put_zt(conn, DATES[9], "000003", 1, "丙")
    res = patterns.detect(conn, DATES)
    w = res["watching"]["refirst"]
    assert [e["code"] for e in w] == ["000003"]
    assert w[0]["meta"]["gap"] >= 1 and -3.0 <= w[0]["meta"]["dip"] <= 2.0


def test_p2_engulf_amplitude():
    """P2：连板≥3 后大阴（振幅≥8%）→ 次日实体吞没触发；振幅不足 → 不触发。"""
    conn = make_conn()
    put_k(conn, "000004", [
        (DATES[0], 10.0, 11.0, 10.0, 11.0),
        (DATES[1], 11.0, 12.1, 11.0, 12.1),
        (DATES[2], 12.1, 13.31, 12.1, 13.31),
        (DATES[3], 13.0, 13.6, 12.0, 12.3),   # 大阴：振幅 12.0%
        (DATES[4], 12.4, 13.6, 12.3, 13.5),   # 阳线收复大阴开盘价 13.0
    ])
    for i, lbv in enumerate((1, 2, 3)):
        put_zt(conn, DATES[i], "000004", lbv, "丁")
    # E 反例：断板阴振幅仅 4.5%
    put_k(conn, "000005", [
        (DATES[0], 10.0, 11.0, 10.0, 11.0),
        (DATES[1], 11.0, 12.1, 11.0, 12.1),
        (DATES[2], 12.1, 13.31, 12.1, 13.31),
        (DATES[3], 13.3, 13.4, 12.8, 12.9),
        (DATES[4], 12.9, 13.5, 12.9, 13.5),
    ])
    for i, lbv in enumerate((1, 2, 3)):
        put_zt(conn, DATES[i], "000005", lbv, "戊")
    res = patterns.detect(conn, DATES)
    f = res["fired"]["engulf"]
    assert [e["code"] for e in f] == ["000004"]
    assert f[0]["date"] == DATES[4] and f[0]["meta"]["amp"] >= 8.0
    assert f[0]["meta"]["lb"] == 3
    assert all(e["code"] != "000005" for e in f)


def test_p3_mareb_fired_and_watching():
    """P3：连板≥2 回踩 MA10 → 阳线反包 fired；未反包未破位 → watching。"""
    base = [(DATES[i], 11.0, 11.05, 10.95, 11.0) for i in range(10)]
    conn = make_conn()
    # F 正例：D11/D12 连板 → D13 回踩 MA10（低点 11.15 < 11.361*1.02）→ D14 反包
    put_k(conn, "000006", base + [
        (DATES[10], 11.0, 12.1, 10.99, 12.1),
        (DATES[11], 12.1, 13.31, 12.05, 13.31),
        (DATES[12], 11.6, 11.7, 11.15, 11.2),   # 回踩：低点距 MA10(11.361) -1.9%
        (DATES[13], 11.2, 12.0, 11.1, 11.9),    # 阳线收盘 11.9 > 前日最高 11.7
    ])
    put_zt(conn, DATES[10], "000006", 1, "己")
    put_zt(conn, DATES[11], "000006", 2, "己")
    # G 反例（watching 分支）：D14 阴线未反包，但收盘仍在 MA10×0.95 上方
    put_k(conn, "000007", base + [
        (DATES[10], 11.0, 12.1, 10.99, 12.1),
        (DATES[11], 12.1, 13.31, 12.05, 13.31),
        (DATES[12], 11.6, 11.7, 11.15, 11.2),
        (DATES[13], 11.3, 11.4, 11.05, 11.1),   # 未反包未破位
    ])
    put_zt(conn, DATES[10], "000007", 1, "庚")
    put_zt(conn, DATES[11], "000007", 2, "庚")
    res = patterns.detect(conn, DATES)
    f = res["fired"]["mareb"]
    assert [e["code"] for e in f] == ["000006"]
    assert f[0]["date"] == DATES[13]
    assert -3.0 <= f[0]["meta"]["ma_dev"] <= 2.0
    w = res["watching"]["mareb"]
    assert [e["code"] for e in w] == ["000007"]
    assert all(e["code"] != "000006" for e in w)


def test_counts_and_today_events():
    """counts 汇总与 today_events（F 的触发日恰为窗口最后一天）。"""
    base = [(DATES[i], 11.0, 11.05, 10.95, 11.0) for i in range(10)]
    conn = make_conn()
    put_k(conn, "000008", base + [
        (DATES[10], 11.0, 12.1, 10.99, 12.1),
        (DATES[11], 12.1, 13.31, 12.05, 13.31),
        (DATES[12], 11.6, 11.7, 11.15, 11.2),
        (DATES[13], 11.2, 12.0, 11.1, 11.9),
    ])
    put_zt(conn, DATES[10], "000008", 1, "辛")
    put_zt(conn, DATES[11], "000008", 2, "辛")
    res = patterns.detect(conn, DATES)
    assert res["today"] == DATES[-1]
    assert res["counts"]["mareb"]["fired_today"] == 1
    assert res["counts"]["mareb"]["fired"] == 1
    assert len(res["today_events"]) == 1
    assert res["today_events"][0]["key"] == "mareb"
    assert res["window"]["end"] == DATES[-1]


def test_empty_db():
    """空库不炸、结构完整。"""
    conn = make_conn()
    res = patterns.detect(conn, DATES)
    assert res["today_events"] == []
    assert set(res["counts"]) == {"refirst", "engulf", "mareb"}


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
