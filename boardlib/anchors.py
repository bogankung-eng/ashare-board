# -*- coding: utf-8 -*-
"""P20 · 周期锚定链：属性簇引擎 + 锚状态 + 关系链节点。

设计约束（对应主人 2026-11-10 确认的 ②+③ 方案）：
1. 属性簇真值直接取 zt_reasons.reason 里现成的属性标签（「东方」/「羊」字辈…），
   不按单字拆、不做 NLP —— 因此「东方」不会被拆成 东/方，阳/洋/羊 不会被拆散。
2. 跨 60 交易日窗口在 Python 侧一次算完，作为顶层 payload 输出，
   避开 P12 数据分片（前端只有最近 5 日 days）导致的链条断裂。
3. 锚状态用 kline OHLCV 量化（在板 / 横盘不倒 / 破位失效），不靠主观印象。
4. 纯离线、零第三方依赖、零网络请求；不 import analysis，避免循环依赖。
"""
import re
from collections import defaultdict

MAX_WINDOW = 60
MIN_STOCKS = 3          # 窗口内至少 3 只不同股票才算「共识簇」
MIN_ACTIVE_DAYS = 2     # 至少出现 2 个交易日
MAX_MEMBERS = 24
MAX_EVENTS = 20
STATE_KLINE_N = 10

# 「东方」是双字属性，「羊」是谐音字辈，两种形式都在 reason 里带引号或「X字辈」
_QUOTED = re.compile(r'[\u201c"\u300c]([^\u201d"\u300d]{1,6})[\u201d"\u300d]')
_BARE = re.compile(r'([\u4e00-\u9fff]{1,2})字辈')
# 引号里偶尔出现的非属性词，配合 MIN_STOCKS / MIN_ACTIVE_DAYS 一起降噪
_STOP = {"一字", "次新", "新股", "重组", "复牌", "摘帽", "涨停", "连板", "超跌",
         "反包", "首板", "龙头", "高度", "空间", "补涨", "回暖", "退潮", "唯一"}


def norm_tag(s):
    """归一化簇名：去「字辈」尾、只留 1-4 个汉字、滤掉噪声词。"""
    s = (s or "").strip()
    if s.endswith("字辈"):
        s = s[:-2]
    if not s or len(s) > 4:
        return ""
    if not all("\u4e00" <= c <= "\u9fff" for c in s):
        return ""
    if s in _STOP:
        return ""
    return s


def extract_tags(reason):
    """从一条涨停原因里抽出属性标签集合。"""
    out = set()
    r = reason or ""
    for m in _QUOTED.finditer(r):
        t = norm_tag(m.group(1))
        if t:
            out.add(t)
    for m in _BARE.finditer(r):
        t = norm_tag(m.group(1))
        if t:
            out.add(t)
    return out


def _iso(d):
    d = str(d)
    return d[:4] + "-" + d[4:6] + "-" + d[6:8] if len(d) == 8 else d


def state_of(conn, code, last_zt_day, today_codes):
    """锚状态：今日在板 > 末板后 N 根 K 线的涨跌/振幅 → 横盘不倒 / 走弱 / 破位。"""
    if code in today_codes:
        return {"key": "onboard", "label": "在板", "chg": None, "amp": None,
                "detail": "今日仍封板 · 锚持续"}
    ld = _iso(last_zt_day)
    try:
        base = conn.execute(
            "SELECT close FROM kline WHERE code=? AND date=?", (code, ld)).fetchone()
        rows = conn.execute(
            "SELECT date,close,high,low FROM kline WHERE code=? AND date>? ORDER BY date LIMIT ?",
            (code, ld, STATE_KLINE_N)).fetchall()
    except Exception:
        base, rows = None, []
    if not rows:
        return {"key": "new", "label": "新板", "chg": None, "amp": None,
                "detail": "末板后暂无后续 K 线"}
    b = float(base[0]) if base and base[0] else float(rows[0][1])
    end = float(rows[-1][1])
    hi = max(float(r[2] or 0) for r in rows)
    lo = min(float(r[3] or 0) for r in rows if r[3])
    chg = round((end / b - 1) * 100, 1) if b else 0.0
    amp = round((hi / lo - 1) * 100, 1) if lo else 0.0
    if chg <= -10:
        key, label = "broken", "破位失效"
    elif chg >= -5 and amp <= 25:
        key, label = "platform", "横盘不倒"
    else:
        key, label = "shaky", "走弱观察"
    return {"key": key, "label": label, "chg": chg, "amp": amp,
            "detail": "末板后 %d 根 K 线 %+.1f%% · 振幅 %.1f%%" % (len(rows), chg, amp)}


def chain_state_of(alive, state_key):
    """链的生命周期：健康 / 锚失效待接力 / 已结束。"""
    if not alive:
        return {"key": "ended", "label": "链已结束", "hint": "簇不再活跃"}
    if state_key in ("onboard", "platform", "new"):
        return {"key": "healthy", "label": "链健康", "hint": "锚仍在，簇延续"}
    return {"key": "relay", "label": "锚失效 · 待接力",
            "hint": "老锚走弱但簇仍活跃，关注新锚或属性切换"}


def _events(tag, dlist, anchor, astate, first_day, last_day, peak, today, chain_state):
    ev = [{"date": first_day, "type": "首现", "text": tag + " 属性首次成簇"}]
    hi = max(dlist, key=lambda x: x["max_lb"]) if dlist else None
    if hi and hi["max_lb"] >= 2 and hi["date"] != first_day:
        ev.append({"date": hi["date"], "type": "锚确立",
                   "text": "%s 最高 %d 板，锚位确立" % (anchor["name"], hi["max_lb"])})
    if peak and peak["count"] >= 4:
        ev.append({"date": peak["date"], "type": "扩散峰值",
                   "text": "同属性 %d 只涨停，共识峰值" % peak["count"]})
    lab = {"platform": "锚横盘不倒 · 链仍有效", "broken": "锚破位 · 链失效",
           "onboard": "锚今日仍在板 · 链延续", "shaky": "锚走弱 · 观察是否切换",
           "new": "锚新板 · 待确认"}.get(astate["key"], "")
    if lab:
        ev.append({"date": last_day, "type": "锚状态",
                   "text": "%s：%s" % (anchor["name"], lab)})
    if chain_state["key"] == "relay":
        ev.append({"date": last_day, "type": "节点切换",
                   "text": "老锚失效但同属性仍有 %d 只涨停 → 找新锚 / 看属性接力"
                   % (dlist[-1]["count"] if dlist else 0)})
    if last_day != today:
        ev.append({"date": last_day, "type": "簇降温", "text": "末次活跃，之后未再成簇"})
    ev.sort(key=lambda e: e["date"])
    return ev


def _empty():
    return {"window": [], "window_days": 0, "label_since": "", "clusters": [],
            "relays": [], "switches": [], "today": "",
            "summary": {"total": 0, "alive": 0, "healthy": 0, "relay": 0,
                        "anchors_ok": 0, "peak": 0}}


def build_anchor(conn, days, dates, window=MAX_WINDOW, switches=None):
    """主入口：返回可直接塞进 payload 的锚定链数据（与日期切换无关）。"""
    if not dates:
        return _empty()
    win = list(dates[-window:])
    today = win[-1]

    # ① 逐日涨停池 + 每只股票最后一次涨停日（锚状态基准）
    zt_by_day, last_zt = {}, {}
    for d in win:
        zt = ((days.get(d) or {}).get("pools") or {}).get("zt") or []
        zt_by_day[d] = zt
        for r in zt:
            c = str(r.get("代码") or "")
            if c:
                last_zt[c] = d
    today_codes = {str(r.get("代码") or "") for r in zt_by_day.get(today, [])}

    # ② 属性标签 → 逐簇逐日成员（标签只覆盖有涨停原因的交易日）
    reasons = defaultdict(dict)
    try:
        for d, c, rs in conn.execute(
                "SELECT date,code,reason FROM zt_reasons "
                "WHERE date>=? AND date<=? AND reason!=''", (win[0], win[-1])):
            reasons[str(d)][str(c)] = rs or ""
    except Exception:
        pass
    by_tag = defaultdict(lambda: defaultdict(list))
    for d in win:
        rm = reasons.get(str(d), {})
        for r in zt_by_day.get(d, []):
            code = str(r.get("代码") or "")
            tags = extract_tags(rm.get(code, ""))
            if not tags:
                continue
            item = {"code": code, "name": str(r.get("名称") or ""),
                    "lb": int(r.get("连板数") or 0),
                    "ind": str(r.get("所属行业") or "其他"),
                    "reason": rm.get(code, "")}
            for t in tags:
                by_tag[t][d].append(item)

    # ③ 组装每条链
    clusters = []
    for tag, dmap in by_tag.items():
        codes = {m["code"] for ms in dmap.values() for m in ms}
        if len(codes) < MIN_STOCKS or len(dmap) < MIN_ACTIVE_DAYS:
            continue
        dlist = []
        for d in win:
            if d in dmap:
                ms = dmap[d]
                dlist.append({"date": d, "count": len(ms),
                              "max_lb": max((m["lb"] for m in ms), default=0),
                              "names": [m["name"] for m in ms][:8]})
        prof = {}
        for d in win:
            for m in dmap.get(d, []):
                p = prof.setdefault(m["code"], {
                    "code": m["code"], "name": m["name"], "first_day": d,
                    "last_day": d, "max_lb": 0, "days": 0,
                    "ind": m["ind"], "reason": m["reason"]})
                p["last_day"] = d
                p["days"] += 1
                p["max_lb"] = max(p["max_lb"], m["lb"])
        # 锚 = 高度最高 → 最早走出 → 出现天数最多（主人说的「最先涨起来/走出来」）
        anchor = sorted(prof.values(),
                        key=lambda p: (-p["max_lb"], p["first_day"], -p["days"], p["code"]))[0]
        astate = state_of(conn, anchor["code"],
                          last_zt.get(anchor["code"], anchor["last_day"]), today_codes)
        peak = max(dlist, key=lambda x: x["count"])
        members = sorted(prof.values(), key=lambda p: (p["first_day"], -p["max_lb"], p["code"]))
        first_day, last_day = dlist[0]["date"], dlist[-1]["date"]
        alive = last_day == today and dlist[-1]["count"] >= 2
        chain_state = chain_state_of(alive, astate["key"])
        clusters.append({
            "key": tag, "label": tag, "first_day": first_day, "last_day": last_day,
            "span": len(dlist), "today": dlist[-1]["count"] if last_day == today else 0,
            "peak": {"date": peak["date"], "count": peak["count"]},
            "alive": alive, "chain_state": chain_state,
            "anchor": anchor, "anchor_state": astate,
            "first_movers": [{"code": p["code"], "name": p["name"],
                              "first_day": p["first_day"], "max_lb": p["max_lb"]}
                             for p in members[:5]],
            "members": members[:MAX_MEMBERS], "member_total": len(prof),
            "days": dlist,
            "events": _events(tag, dlist, anchor, astate, first_day, last_day,
                              peak, today, chain_state)[:MAX_EVENTS],
        })
    clusters.sort(key=lambda c: (not c["alive"], -c["today"], -c["peak"]["count"],
                                 -c["span"], c["key"]))

    # ④ 属性接力：旧簇达峰后 10 个交易日内新簇首现 = 有效节点切换
    idx = {d: i for i, d in enumerate(win)}
    relays = []
    for c in sorted(clusters, key=lambda x: x["first_day"]):
        prev = [x for x in clusters
                if x["first_day"] < c["first_day"] and x["peak"]["count"] >= 3]
        if not prev:
            continue
        src = max(prev, key=lambda x: (x["peak"]["date"], x["peak"]["count"]))
        gap = idx.get(c["first_day"], 0) - idx.get(src["peak"]["date"], 0)
        if gap < 0 or gap > 10:
            continue
        relays.append({"from": src["key"], "to": c["key"], "date": c["first_day"],
                       "from_peak": src["peak"]["date"], "to_count": c["today"],
                       "gap": gap})

    label_since = ""
    try:
        label_since = str(conn.execute(
            "SELECT MIN(date) FROM zt_reasons WHERE reason!=''").fetchone()[0] or "")
    except Exception:
        pass
    return {
        "window": win, "window_days": len(win), "label_since": label_since,
        "clusters": clusters, "relays": relays[:8], "switches": switches or [],
        "today": today,
        "summary": {
            "total": len(clusters),
            "alive": sum(1 for c in clusters if c["alive"]),
            "healthy": sum(1 for c in clusters if c["chain_state"]["key"] == "healthy"),
            "relay": sum(1 for c in clusters if c["chain_state"]["key"] == "relay"),
            "anchors_ok": sum(1 for c in clusters
                              if c["anchor_state"]["key"] in ("onboard", "platform")),
            "peak": max((c["peak"]["count"] for c in clusters), default=0),
        },
    }


def annotate_leaders(conn, catchup, days, dates):
    """③ 地基：给补涨雷达的龙头档案补锚状态。

    刻意不改动 analyze_catchup 的「在板且可上车 → 不触发」过滤语义，
    只在数据层补信息，避免破坏 P14 既有行为。
    """
    if not dates:
        return catchup
    last_zt, today_codes = {}, set()
    for d in dates:
        for r in ((days.get(d) or {}).get("pools") or {}).get("zt") or []:
            c = str(r.get("代码") or "")
            if c:
                last_zt[c] = d
    for r in ((days.get(dates[-1]) or {}).get("pools") or {}).get("zt") or []:
        today_codes.add(str(r.get("代码") or ""))
    for l in (catchup or {}).get("leaders", []):
        L = l.get("leader") or {}
        code = L.get("code", "")
        L["anchor_state"] = state_of(
            conn, code, last_zt.get(code, L.get("last_zt_day", dates[-1])), today_codes)
    return catchup


def cluster_brief(payload, limit=12):
    """给字辈挖掘用的属性簇简表（③ 共用口径，不拆单字）。"""
    return [{"key": c["key"], "label": c["label"], "today": c["today"],
             "peak": c["peak"]["count"], "first_day": c["first_day"],
             "alive": c["alive"], "member_total": c["member_total"],
             "anchor": c["anchor"]["name"], "state": c["anchor_state"]["label"],
             "chain": c["chain_state"]["label"]}
            for c in (payload.get("clusters") or [])[:limit]]
