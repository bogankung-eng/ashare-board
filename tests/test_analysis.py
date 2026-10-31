# -*- coding: utf-8 -*-
"""boardlib.analysis 快照测试。

设计要点：
  - 输入 = 本地 board.db 最近 3 个交易日（历史池子固定，跨日采集不失效）
  - 不触网：不调用 fetch_quotes / load_unlock（行情与解禁是时变数据）
  - 断言四类：结构（key 集合）/ 范围（比例域）/ 排序稳定性 / 确定性（同输入两次一致）
  - 拆分/重构后的回归安全网：任何输出结构变化在此暴露
"""
import os
import sqlite3
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import boardlib.analysis as A  # noqa: E402
from boardlib.config import DB  # noqa: E402


@pytest.fixture(scope="module")
def dates():
    conn = sqlite3.connect(DB)
    ds = A.load_dates(conn)
    conn.close()
    return ds


@pytest.fixture(scope="module")
def days(dates):
    """最近 3 个交易日的完整日数据（与 build() 同构）。"""
    d3 = dates[-3:]
    conn = sqlite3.connect(DB)
    out = {}
    for d in d3:
        pools, breadth = A.load_day(conn, d)
        sent = A.sentiment(pools, breadth)
        A.analyze_stocks(pools, sent)
        themes, hl = A.analyze_themes(pools, sent)
        ext = A.load_ext(conn, d)
        out[d] = {"pools": pools, "breadth": breadth, "sent": sent,
                  "themes": themes, "hl": hl, "ext": A.analyze_ext(ext, pools)}
    conn.close()
    return out, d3


# ---------- 日期与池子 ----------

def test_load_dates(dates):
    assert len(dates) >= 40, "交易日窗口应有 40+ 天"
    assert all(len(d) == 8 and d.isdigit() for d in dates)
    assert dates == sorted(dates), "日期应升序"


def test_load_day_pools(dates):
    conn = sqlite3.connect(DB)
    pools, breadth = A.load_day(conn, dates[-1])
    conn.close()
    assert set(pools) == {"zt", "dt", "zb"}
    assert pools["zt"], "最新交易日涨停池不应为空"
    zt_keys = set(pools["zt"][0])
    assert {"代码", "名称", "连板数", "所属行业", "首次封板时间"} <= zt_keys
    assert breadth and breadth["limit_up"] > 0


def test_sentiment_structure(days):
    dd, _ = days
    s = dd[sorted(dd)[-1]]["sent"]
    for k in ("zt", "dt", "tag", "tag_cls"):
        assert k in s, f"sentiment 缺 {k}"


# ---------- 晋级率 ----------

def test_promotion(days):
    dd, d3 = days
    p = A.analyze_promotion(dd, d3)
    assert isinstance(p, list) and p, "promotion 应非空"
    for row in p:
        assert {"ind", "n", "fb", "fb_rate", "j12", "j12_rate"} <= set(row)
        for r in ("fb_rate", "j12_rate", "j23_rate", "j34_rate"):
            if row.get(r) is not None:
                assert 0 <= row[r] <= 100, f"{row['ind']}.{r} 越界"


def test_promotion_deterministic(days):
    dd, d3 = days
    assert A.analyze_promotion(dd, d3) == A.analyze_promotion(dd, d3)


# ---------- 字辈挖掘 ----------

def test_nameplay_snapshot(days):
    dd, d3 = days
    np_ = A.analyze_nameplay(dd, d3)
    assert set(np_) == {"active", "watch", "days"}
    for c in np_["active"]:
        assert c["today"] >= 3, "活跃字辈阈值 ≥3"
        assert c["max_lb"] >= 1 and c["members"]
        assert len(c["hist"]) == len(d3)
    for c in np_["watch"]:
        assert c["today"] == 2


def test_nameplay_sort_stable(days):
    """P11b 修复的平局抖动回归：排序必须含 ch 尾键，输出次序确定。"""
    dd, d3 = days
    np_ = A.analyze_nameplay(dd, d3)
    exp_act = sorted(np_["active"], key=lambda x: (-x["today"], -x["max_lb"], -x["streak"], x["ch"]))
    exp_wat = sorted(np_["watch"], key=lambda x: (-x["max_lb"], -x["streak"], x["ch"]))
    assert np_["active"] == exp_act
    assert np_["watch"] == exp_wat


def test_nameplay_deterministic(days):
    dd, d3 = days
    assert A.analyze_nameplay(dd, d3) == A.analyze_nameplay(dd, d3)


# ---------- 时间线 ----------

def test_day_timeline_snapshot(days, dates):
    tl = A.analyze_day_timeline(days[0], dates)
    assert tl["n_up"] > 0 and tl["max_lb"] >= 1
    assert tl["n_up"] + tl["n_zb"] == len(tl["events"])
    for e in tl["events"]:
        assert 540 <= e["t"] <= 930, f"封板时间应落在交易时段: {e}"
        assert e["kind"] in ("up", "zb")


def test_period_timeline_snapshot(days, dates):
    dd, _ = days
    d3 = sorted(dd)[-3:]
    week = A.analyze_period_timeline(dd, d3, 5)
    month = A.analyze_period_timeline(dd, d3, 22)
    assert len(week["dates"]) == 3, "数据只有 3 天时窗口取全量"
    assert len(month["days"]) == 3
    for e in week["days"] + month["days"]:
        assert {"date", "zt", "dt", "zb", "maxlb"} <= set(e)
        assert e["zt"] >= 0 and e["maxlb"] >= 0
    for node in week["nodes"] + month["nodes"]:
        assert node["type"] in ("high", "break", "ice", "hot")


# ---------- 题材与封板 ----------

def test_themes_structure(days):
    dd, _ = days
    last = sorted(dd)[-1]
    themes = dd[last]["themes"]
    assert themes, "themes 应非空"
    assert {"名称", "count", "max_lb", "leader"} <= set(themes[0])
    for t in themes:
        assert t["count"] >= 1 and t["leader"]["名称"]


def test_seal_time_buckets(days):
    dd, _ = days
    last = sorted(dd)[-1]
    st = A.analyze_seal_time(dd[last]["pools"])
    assert st["total"] > 0
    assert sum(b["n"] for b in st["buckets"]) == st["total"]
    assert sum(b["pct"] for b in st["buckets"]) in (99, 100, 101), "五桶百分比取整后应接近 100"


# ---------- P12 数据分片 ----------

def test_write_history_split_and_trim(tmp_path):
    import boardlib.analysis as A
    d1, d2 = {"zt": [], "dt": [], "zb": []}, {"zt": [], "dt": [], "zb": []}
    data = {"days": {"20260901": d1, "20261001": d2},
            "dates": ["20260901", "20261001"]}
    out = tmp_path / "history"
    trimmed = A.write_history(dict(data), out_dirs=[str(out)])
    assert (out / "history_202609.json").exists()
    assert (out / "history_202610.json").exists()
    assert set(trimmed["days"]) <= {"20260901", "20261001"}  # ≤ RECENT_DAYS
    assert trimmed["historyMonths"] == ["202609", "202610"]


def test_write_history_merge_keeps_existing(tmp_path):
    """--date 单日调试模式不得清掉既有历史月份。"""
    import json as J
    import boardlib.analysis as A
    out = tmp_path / "history"
    out.mkdir()
    old = {"20260815": {"zt": [], "dt": [], "zb": []}}
    (out / "history_202608.json").write_text(J.dumps(old), encoding="utf-8")
    data = {"days": {"20261009": {"zt": [], "dt": [], "zb": []}}, "dates": ["20261009"]}
    A.write_history(dict(data), out_dirs=[str(out)])
    merged = J.loads((out / "history_202608.json").read_text(encoding="utf-8"))
    assert "20260815" in merged, "既有历史月份不得丢失"


def test_seal_quality_structure(days):
    dd, d3 = days
    sq = A.analyze_seal_quality(dd, d3)
    assert sq is not None
    assert {"gap", "refeng", "refeng_n", "funds", "cur_max", "prev_max"} <= set(sq)
    if sq["refeng"] is not None:
        assert 0 <= sq["refeng"] <= 100
    for f in sq["funds"]:
        assert f["cur"] is None or f["cur"] >= 0
        assert f["prev"] is None or f["prev"] >= 0
    assert sq["cur_max"] >= 0 and sq["prev_max"] >= 0
