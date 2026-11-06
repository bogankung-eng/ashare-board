# -*- coding: utf-8 -*-
"""P19 资讯雷达单测：全部离线，不触网、不碰真实 DB。"""
import sqlite3
from datetime import datetime

from boardlib import radar
from boardlib.analysis import load_radar


RSS = ('''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>T</title>
<item><title>AI 芯片订单增长</title><link>https://x.com/1</link>
<pubDate>Fri, 06 Nov 2026 10:30:00 GMT</pubDate>
<description>&lt;p&gt;摘要 &lt;b&gt;测试&lt;/b&gt;&lt;/p&gt;</description></item>
</channel></rss>''').encode("utf-8")

ATOM = ('''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom 标题</title><link href="https://a.com/1"/>
<updated>2026-11-06T20:00:00Z</updated><summary>摘要</summary></entry></feed>''').encode("utf-8")


def test_parse_feed_rss():
    items = radar.parse_feed(RSS, "S", "ai", "AI / \u5927\u6a21\u578b")
    assert len(items) == 1
    it = items[0]
    assert it["title"] == "AI \u82af\u7247\u8ba2\u5355\u589e\u957f"
    assert it["link"] == "https://x.com/1"
    assert it["pub_dt"] == datetime(2026, 11, 6, 18, 30)  # GMT -> \u5317\u4eac
    assert "\u6458\u8981" in it["summary"] and "<b>" not in it["summary"]
    assert it["track"] == "ai" and it["source"] == "S"


def test_parse_feed_atom_namespace_and_href():
    items = radar.parse_feed(ATOM, "S", "tech", "T")
    assert len(items) == 1
    assert items[0]["link"] == "https://a.com/1"
    assert items[0]["pub_dt"] == datetime(2026, 11, 7, 4, 0)  # UTC -> \u5317\u4eac +8


def test_parse_feed_repairs_truncated_body():
    # \u5927 feed \u88ab\u5206\u5757\u8bfb\u53d6\u622a\u65ad\u65f6\uff0c\u5e94\u9000\u5230\u6700\u540e\u4e00\u4e2a\u5b8c\u6574 </item> \u540e\u8865\u95ed\u5408\u6807\u7b7e
    cut = RSS[:RSS.index(b"</item>") + len(b"</item>")]
    assert b"</channel>" not in cut
    items = radar.parse_feed(cut, "S", "ai", "AI")
    assert len(items) == 1
    assert items[0]["title"].startswith("AI")


def test_parse_time_formats():
    assert radar.parse_time("Fri, 06 Nov 2026 10:30:00 GMT") == datetime(2026, 11, 6, 18, 30)
    assert radar.parse_time("2026-11-06T12:00:00+08:00") == datetime(2026, 11, 6, 12, 0)
    assert radar.parse_time("2026-11-06 09:00:00") == datetime(2026, 11, 6, 17, 0)
    assert radar.parse_time("") is None
    assert radar.parse_time("not-a-date") is None


def test_redline_keywords():
    kws = ["bitcoin", "\u8d4c\u535a", "kalshi"]
    assert radar.is_redline("xxx Bitcoin ETF", kws) is True
    assert radar.is_redline("Kalshi \u9884\u6d4b\u5e02\u573a", kws) is True
    assert radar.is_redline("\u666e\u901a\u79d1\u6280\u65b0\u95fb", kws) is False


def test_fetch_all_filters_dedup_sort_and_quota(monkeypatch):
    cfg = {
        "fetch": {"per_source": 6, "timeout": 6, "recent_days": 7},
        "industries": [{"key": "ai", "name": "AI / \u5927\u6a21\u578b"},
                       {"key": "macro", "name": "\u8d22\u7ecf / \u5b8f\u89c2"}],
        "sources": [{"name": "A", "hint": "ai", "url": "x"},
                    {"name": "B", "hint": "macro", "url": "y"}],
        "redline_keywords": ["bitcoin", "\u8d4c\u535a"],
    }

    def mk(title, dt, link, track, source):
        return {"pub_dt": dt, "title": title, "summary": "", "link": link,
                "source": source, "track": track, "track_name": "X"}

    def fake(src, track_names, timeout, per_source, ctx):
        if src["name"] == "A":
            its = [
                mk("AI \u4e2d\u6587\u6807\u9898", datetime(2026, 11, 6, 20, 0), "u1", "ai", "A"),
                mk("Bitcoin \u8d4c\u535a", datetime(2026, 11, 6, 21, 0), "u2", "ai", "A"),
                mk("AI \u4e2d\u6587\u6807\u9898", datetime(2026, 11, 6, 20, 0), "u1", "ai", "A"),
                mk("\u592a\u65e7", datetime(2026, 10, 1, 0, 0), "u3", "ai", "A"),
            ]
        else:
            its = [mk("Macro EN", datetime(2026, 11, 6, 22, 0), "u4", "macro", "B")]
        return {"source": src["name"], "track": src["hint"],
                "track_name": track_names.get(src["hint"], ""),
                "ok": True, "count": 0, "err": "", "ms": 1, "_items": its}

    monkeypatch.setattr(radar, "_fetch_one", fake)
    items, status = radar.fetch_all(cfg, sources=cfg["sources"],
                                    now=datetime(2026, 11, 7, 0, 0), max_items=50)
    titles = [i["title"] for i in items]
    assert "Bitcoin \u8d4c\u535a" not in titles      # \u5408\u89c4\u7ea2\u7ebf
    assert "\u592a\u65e7" not in titles                # 7 \u5929\u65f6\u6548
    assert titles.count("AI \u4e2d\u6587\u6807\u9898") == 1  # \u53bb\u91cd
    assert items[0]["title"] == "Macro EN"           # \u5168\u5c40\u65f6\u95f4\u5012\u5e8f
    assert any(i["lang"] == "zh" for i in items)
    assert len(status) == 2
    assert all(not k.startswith("_") for s in status for k in s)  # \u79c1\u6709\u5b57\u6bb5\u5df2\u6e05\u7406


def test_track_list_from_project_config():
    tracks = radar.track_list()
    assert len(tracks) == 12
    assert all("key" in t and "name" in t for t in tracks)


def test_load_radar_missing_tables_is_safe(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "empty.db"))
    r = load_radar(conn)
    assert r["items"] == [] and r["tracks"] == [] and r["total"] == 0
    conn.close()
