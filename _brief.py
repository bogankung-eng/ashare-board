#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股复盘简报生成器：读 board.html → 输出当日盘后简报（情绪/龙头/异动/席位/潜龙/昨日验证）
供每日自动化汇报使用：python _brief.py
"""
import json
import os
import re
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(BASE, "board.html")
DB = os.path.join(BASE, "data", "board.db")


def load_board():
    html = open(BOARD, encoding="utf-8").read()
    m = re.search(r"window\.BOARD_DATA = (\{.*?\});\n</script>", html, re.S)
    return json.loads(m.group(1))


def prev_map(nxt):
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT code, data_json FROM prev_zt WHERE date=?", (nxt,)).fetchall()
    conn.close()
    return {code: json.loads(j) for code, j in rows}


def backtest_prev(d, nxt, days):
    """昨日延续性评分 → 今日验证（返回简略字符串）"""
    if nxt not in days:
        return None
    pm = prev_map(nxt)
    day = days[d]
    groups = {"强": [], "中": [], "弱": []}
    for r in day["pools"]["zt"]:
        lv = (r.get("_analysis") or {}).get("level", "中")
        p = pm.get(r["代码"])
        if p:
            groups[lv].append(p)
    parts = []
    for lv in ["强", "中"]:
        arr = groups[lv]
        if not arr:
            continue
        pcts = [float(r.get("涨跌幅") or 0) for r in arr]
        avg = sum(pcts) / len(pcts)
        jn = sum(1 for r in arr if abs(float(r.get("最新价") or 0) - float(r.get("涨停价") or 0)) / max(float(r.get("涨停价") or 1), 1) < 0.001)
        parts.append(f"{lv}组({len(arr)}只)次日{avg:+.1f}%/晋级{jn/len(arr)*100:.0f}%")
    return " · ".join(parts) if parts else None


def main():
    data = load_board()
    days = data["days"]
    dates = [x for x in data["dates"] if x in days]
    d = dates[-1]
    day = days[d]
    wd = "一二三四五六日"[int(d[6:8]) % 7 if False else (int(d[6:8]) + 1) % 7]
    sent, leaders, seats, dragons = day["sent"], day["leaders"], day["seats"], day["dragons"]
    mv = data.get("movement") or {"alerts": [], "n_hot": 0}

    L = []
    L.append(f"📊 **A股复盘简报 {d[:4]}-{d[4:6]}-{d[6:]}**")
    L.append("━━━━━━━━━━━━━━━")
    # 情绪
    L.append(f"【情绪】{sent['tag']} · 涨停{sent['zt']} 跌停{sent['dt']} 炸板率{sent['zbrate']}% 最高板{sent['max_lb']}板")
    # 龙头
    t, e = leaders.get("total"), leaders.get("emo")
    if t and e:
        t_s = f"{t['name']}{'·今日涨停' if t['today'] else '·今日断板⚠️'}"
        L.append(f"【龙头】总龙 {t_s} | 情绪龙 {e['name']} {e['lb']}板(评分{e['score']})")
        for s in leaders.get("signals", [])[:2]:
            mark = {"danger": "⚠️", "warn": "❗", "good": "✅", "ok": "—"}.get(s["cls"], "·")
            L.append(f"   {mark} {s['text']}")
    # 异动
    hot = [a for a in mv.get("alerts", []) if a["level"] in ("T1", "T2")]
    if hot:
        top3 = "、".join(f"{a['name']}+{max(a['g20'], a['g30']):.0f}%" for a in hot[:3])
        L.append(f"【异动】T1/T2预警 {len(hot)} 只：{top3}")
    elif mv.get("alerts"):
        L.append(f"【异动】T0观察 {len(mv['alerts'])} 只（接近阈值）")
    else:
        L.append("【异动】无触发")
    # 席位
    hm = [h for h in seats.get("hot", []) if h["net"] != 0]
    if hm:
        buys = sum(1 for h in hm if h["net"] > 0)
        sells = sum(1 for h in hm if h["net"] < 0)
        net_all = sum(h["net"] for h in hm)
        L.append(f"【席位】知名游资净{(net_all/1e4):+.0f}万（买{buys}笔/卖{sells}笔）")
        top = hm[0]
        L.append(f"   最显著：{top['name']} {top['seat'][:12]}… {'+' if top['net']>0 else ''}{top['net']/1e4:.0f}万")
    else:
        L.append("【席位】当日无知名游资动作")
    # 潜龙
    if dragons.get("pool"):
        top3 = "、".join(f"{c['name']}({c['score']}分)" for c in dragons["pool"][:3])
        L.append(f"【潜龙】{len(dragons['pool'])} 只候选：{top3}")
    # 昨日验证
    if len(dates) >= 2:
        bt = backtest_prev(dates[-2], d, days)
        if bt:
            L.append(f"【昨日验证】{dates[-2][6:]}日 {bt}")
    L.append("━━━━━━━━━━━━━━━")
    L.append("详见 https://ashare-board.bogan-kung.workers.dev/")
    print("\n".join(L))


if __name__ == "__main__":
    main()
