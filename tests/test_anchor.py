# -*- coding: utf-8 -*-
"""P20 周期锚定链离线单测：不触网、不依赖真实 board.db。"""
import sqlite3

import pytest

from boardlib import anchors

DATES = ["20261102", "20261103", "20261106", "20261109"]


def _row(code, name, lb=1, ind="电气设备"):
    return {"代码": code, "名称": name, "连板数": lb, "所属行业": ind}


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(str(tmp_path / "anchor.db"))
    c.execute("CREATE TABLE zt_reasons(date TEXT, code TEXT, name TEXT, reason TEXT)")
    c.execute("CREATE TABLE kline(code TEXT, date TEXT, open REAL, high REAL, low REAL, "
              "close REAL, volume REAL, amount REAL, pct REAL)")
    reasons = [
        ("20261102", "002242", "九阳股份", "机器人+豆浆机+“羊”字辈"),
        ("20261102", "002086", "东方海洋", "体外诊断+“羊”字辈"),
        ("20261103", "002242", "九阳股份", "机器人+“羊”字辈"),
        ("20261103", "000678", "襄阳轴承", "机器人轴承+羊字辈"),
        ("20261103", "002086", "东方海洋", "体外诊断+“羊”字辈"),
        ("20261106", "603366", "日出东方", "“东方”+储能+光伏"),
        ("20261106", "600776", "东方通信", "“东方”+卫星互联网"),
        ("20261106", "600327", "大东方", "“东方”+百货零售"),
        ("20261109", "603366", "日出东方", "“东方”+储能+光伏"),
        ("20261109", "600776", "东方通信", "“东方”+卫星互联网"),
        ("20261109", "600327", "大东方", "“东方”+百货零售"),
        ("20261109", "000678", "襄阳轴承", "机器人轴承+羊字辈"),
    ]
    c.executemany("INSERT INTO zt_reasons VALUES(?,?,?,?)", reasons)
    # 002242 末板 11/03 后横盘；000678 破位；603366 无后续 K 线
    kl = [
        ("002242", "2026-11-03", 20, 20, 20, 20, 1, 1, 0),
        ("002242", "2026-11-04", 20, 20.5, 19.8, 20.2, 1, 1, 1),
        ("002242", "2026-11-05", 20.2, 20.6, 20, 20.4, 1, 1, 1),
        ("002242", "2026-11-06", 20.4, 20.7, 20.1, 20.5, 1, 1, 1),
        ("000678", "2026-11-09", 18, 18, 18, 18, 1, 1, 0),
        ("000678", "2026-11-10", 18, 18, 15, 15.5, 1, 1, -13),
    ]
    c.executemany("INSERT INTO kline VALUES(?,?,?,?,?,?,?,?,?)", kl)
    c.commit()
    yield c
    c.close()


@pytest.fixture
def days():
    zt = {
        "20261102": [_row("002242", "九阳股份", 2), _row("002086", "东方海洋", 1)],
        "20261103": [_row("002242", "九阳股份", 3), _row("000678", "襄阳轴承", 1),
                     _row("002086", "东方海洋", 2)],
        "20261106": [_row("603366", "日出东方", 1), _row("600776", "东方通信", 1),
                     _row("600327", "大东方", 1)],
        "20261109": [_row("603366", "日出东方", 2), _row("600776", "东方通信", 2),
                     _row("600327", "大东方", 2), _row("000678", "襄阳轴承", 1)],
    }
    return {d: {"pools": {"zt": zt[d], "zb": [], "dt": []}} for d in DATES}


def test_extract_tags_keeps_double_char_and_homophone():
    assert anchors.extract_tags("“东方”+储能+光伏") == {"东方"}
    assert anchors.extract_tags("机器人轴承+羊字辈") == {"羊"}
    assert anchors.extract_tags("体外诊断+“羊字辈”") == {"羊"}
    assert anchors.extract_tags("照明+“羊”字辈") == {"羊"}
    assert anchors.extract_tags("商业航天+激光通信") == set()


def test_norm_tag_filters_noise():
    assert anchors.norm_tag("东方") == "东方"
    assert anchors.norm_tag("羊字辈") == "羊"
    assert anchors.norm_tag("一字") == ""
    assert anchors.norm_tag("AI硬件") == ""
    assert anchors.norm_tag("超长噪声词") == ""


def test_chain_state_three_lifecycle_states():
    assert anchors.chain_state_of(True, "onboard")["key"] == "healthy"
    assert anchors.chain_state_of(True, "platform")["key"] == "healthy"
    assert anchors.chain_state_of(True, "broken")["key"] == "relay"
    assert anchors.chain_state_of(False, "platform")["key"] == "ended"


def test_state_of_uses_kline_not_impression(conn):
    assert anchors.state_of(conn, "603366", "20261109", {"603366"})["key"] == "onboard"
    s = anchors.state_of(conn, "002242", "20261103", set())
    assert s["key"] == "platform" and s["chg"] > 0
    b = anchors.state_of(conn, "000678", "20261109", set())
    assert b["key"] == "broken"
    assert anchors.state_of(conn, "999999", "20261109", set())["key"] == "new"


def test_build_anchor_does_not_split_double_char_or_homophone(conn, days):
    p = anchors.build_anchor(conn, days, DATES)
    by = {c["key"]: c for c in p["clusters"]}
    assert "东方" in by and "东" not in by and "方" not in by
    assert by["东方"]["anchor"]["name"] in {"日出东方", "东方通信", "大东方"}
    assert len(by["东方"]["members"]) == 3
    yang = by["羊"]["members"]
    names = {m["name"] for m in yang}
    assert any("阳" in n for n in names) and any("洋" in n or "海" in n for n in names)
    assert by["羊"]["member_total"] == 3


def test_build_anchor_summary_relay_and_window(conn, days):
    p = anchors.build_anchor(conn, days, DATES)
    assert p["window_days"] == len(DATES)
    assert p["window"] == DATES
    assert p["today"] == DATES[-1]
    assert p["summary"]["total"] == len(p["clusters"])
    assert p["summary"]["peak"] >= 3
    assert any(r["from"] == "羊" and r["to"] == "东方" for r in p["relays"])
    for c in p["clusters"]:
        assert c["chain_state"]["key"] in {"healthy", "relay", "ended"}
        assert c["first_movers"] and c["events"]
        assert all(len(e["text"]) > 0 for e in c["events"])
        assert c["member_total"] >= 3


def test_build_anchor_accepts_switches_and_empty_input(conn, days):
    p = anchors.build_anchor(conn, days, DATES, switches=[{"from_name": "甲"}])
    assert p["switches"] == [{"from_name": "甲"}]
    empty = anchors.build_anchor(conn, {}, [])
    assert empty["clusters"] == [] and empty["summary"]["total"] == 0


def test_cluster_brief_and_annotate_leaders(conn, days):
    p = anchors.build_anchor(conn, days, DATES)
    brief = anchors.cluster_brief(p)
    assert brief and all(set(b) >= {"key", "today", "anchor", "state", "chain"} for b in brief)
    cu = {"leaders": [{"leader": {"code": "002242", "name": "九阳股份"}}]}
    out = anchors.annotate_leaders(conn, cu, days, DATES)
    assert len(out["leaders"]) == 1  # 不改过滤语义，只补字段
    assert out["leaders"][0]["leader"]["anchor_state"]["key"] == "platform"
