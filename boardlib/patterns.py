# -*- coding: utf-8 -*-
"""P23 K线技术形态识别引擎（P1 再次首板 / P2 大阴反包 / P3 均线反包）。

口径主人 2026-11-24 拍板：
- P1 再次首板（refirst）：首板后 2~5 个交易日回调，回调低点进入
  「首板开盘价 -3% ~ +2%」带内即算「回调到位」——允许破一点再回拉、
  允许还差约 2% 就瞬间拉起，不要求收盘不破（紫阳东路式的不完美回调）。
  再次涨停当日触发。
- P2 高位大阴反包（engulf）：连板≥3 次日断板收阴、振幅≥8%（高位大震荡阴，
  实测收盘跌幅口径近 4 个月仅 1~4 次，故弃用），3 个交易日内首次出现
  阳线收盘吞没大阴开盘价（实体反包）触发。
- P3 均线回调反包（mareb）：连板≥2 后 6 日内低点触及 MA10
  （low≤ma*1.02 且 close≥ma*0.97），3 个交易日内阳线收盘反包前日最高触发；
  触及后未反包且现价未破位（≥MA10*0.95）→ watching 待反包。
  「横盘等均线金叉」分支二期。
- 原型样例：冰山冷热 20261110 连板 → 11-13 触 MA10(+6.3%) → 11-16 反包
  （紫阳东路席位 11/03 首现、11/12 与 11/18-19 持续买入）。

涨停判定统一取涨停池 pool_daily（真实口径，连板数东财现成），
窗口 = 最近 60 个交易日（受涨停池回溯覆盖限制）。
识别在 Python 侧一次算完放进顶层 payload（P20 跨周期铁律）。
"""
import json
from collections import defaultdict

WINDOW = 60            # 识别窗口（交易日）
PREHEAT_NATURAL = 45   # kline 回看自然日（保证 MA10 预热）
P1_RE_LOW, P1_RE_HIGH = 0.97, 1.02   # P1 回调带 = 首板开盘价 × [0.97, 1.02]
P1_MAX_GAP = 5         # 首板 → 再板最大间隔（交易日）
P2_MIN_LB = 3          # P2 大阴前最高连板
P2_AMP = 8.0           # P2 大阴振幅阈值（%）
P2_ENGULF_WIN = 3      # P2 反包观察窗（交易日）
P3_MIN_LB = 2          # P3 起点最低连板
P3_TOUCH_WIN = 6       # P3 连板后触及 MA10 的窗口
P3_BAND_UP, P3_BAND_DN = 1.02, 0.97
P3_KEEP = 0.95         # watching 未破位下限（现价 ≥ MA10×0.95）
P3_ENGULF_WIN = 3      # P3 反包观察窗
MAX_FIRED = 40
MAX_WATCH = 24


def _fmt(d):
    """'20261116' -> '11-16'"""
    return d[4:6] + "-" + d[6:8] if d and len(d) == 8 else d


def _ma10(closes, j):
    if j is None or j < 9:
        return None
    return sum(closes[j - 9:j + 1]) / 10.0


def detect(conn, dates):
    """扫描窗口内三形态，返回 {window, today, counts, today_events, fired, watching}。"""
    empty = {"window": {}, "today": None, "counts": {}, "today_events": [],
             "fired": {"refirst": [], "engulf": [], "mareb": []},
             "watching": {"refirst": [], "mareb": []}}
    if not dates:
        return empty
    win = dates[-WINDOW:]
    start_iso = win[0][:4] + "-" + win[0][4:6] + "-" + win[0][6:8]
    today = win[-1]

    ser = defaultdict(list)
    for code, dt, o, h, l, c, pct in conn.execute(
            "SELECT code,date,open,high,low,close,pct FROM kline "
            "WHERE date>=date(?,'-%d day') ORDER BY code,date" % PREHEAT_NATURAL, (start_iso,)):
        if o and h and l and c:
            ser[code].append((dt.replace("-", ""), o, h, l, c, pct))

    zt = defaultdict(set)
    lb = {}
    names = {}
    for dt, code, df in conn.execute(
            "SELECT date,code,data_json FROM pool_daily WHERE pool_type='zt' AND date>=?", (win[0],)):
        d = json.loads(df)
        zt[dt].add(code)
        lb[(dt, code)] = int(d.get("连板数") or 1)
        names[code] = d.get("名称") or names.get(code, "")
    for code, nm in conn.execute("SELECT code,name FROM pool_daily WHERE name IS NOT NULL"):
        names.setdefault(code, nm)

    fired = {"refirst": [], "engulf": [], "mareb": []}
    watch = {"refirst": [], "mareb": []}

    for code, arr in ser.items():
        # 预过滤：窗口内上过涨停板的股票才可能命中（三形态都以连板/首板为前提）
        if not any(code in zt.get(d, ()) for d in win):
            continue
        fpos = {x[0]: j for j, x in enumerate(arr)}
        closes = [x[4] for x in arr]
        n_win = len(win)

        # ---------- P1 再次首板 ----------
        for wi in range(n_win - 3):
            d0 = win[wi]
            if lb.get((d0, code), 0) != 1:
                continue
            j0 = fpos.get(d0)
            if j0 is None:
                continue
            o0 = arr[j0][1]
            hit_k = None
            for k in range(2, P1_MAX_GAP + 1):
                wk = wi + k
                if wk >= n_win:
                    break
                dk = win[wk]
                if code in zt.get(dk, ()):
                    mids = win[wi + 1:wk]
                    if all(code not in zt.get(m, ()) for m in mids):
                        lows = [arr[fpos[m]][3] for m in mids if m in fpos]
                        if lows:
                            lo = min(lows)
                            if o0 * P1_RE_HIGH >= lo >= o0 * P1_RE_LOW:
                                fired["refirst"].append({
                                    "code": code, "name": names.get(code) or code, "date": dk,
                                    "detail": "%s 首板后 %d 天回调至首板开盘价附近（低点 %+.1f%%）再次涨停" % (
                                        _fmt(d0), k, (lo / o0 - 1) * 100),
                                    "meta": {"anchor": d0, "gap": k, "dip": round((lo / o0 - 1) * 100, 1)}})
                    hit_k = k
                    break
            if hit_k is None and wi + P1_MAX_GAP >= n_win - 1:
                last = None
                for k in range(1, min(P1_MAX_GAP, n_win - 1 - wi) + 1):
                    d = win[wi + k]
                    if code in zt.get(d, ()):
                        break
                    j = fpos.get(d)
                    if j is None:
                        continue
                    lo = arr[j][3]
                    if o0 * P1_RE_HIGH >= lo >= o0 * P1_RE_LOW:
                        last = (d, round((lo / o0 - 1) * 100, 1), k)
                if last:
                    watch["refirst"].append({
                        "code": code, "name": names.get(code) or code, "date": last[0],
                        "detail": "%s 首板后第 %d 天回踩首板开盘价（低点 %+.1f%%），等待再次涨停" % (
                            _fmt(d0), last[2], last[1]),
                        "meta": {"anchor": d0, "gap": last[2], "dip": last[1]}})

        # ---------- P2 高位大阴反包 ----------
        for wi in range(1, n_win - 1):
            dprev, d0 = win[wi - 1], win[wi]
            if lb.get((dprev, code), 0) < P2_MIN_LB:
                continue
            if code in zt.get(d0, ()):
                continue
            j0 = fpos.get(d0)
            if j0 is None or j0 == 0:
                continue
            o0, h0, l0, c0 = arr[j0][1:5]
            prev_c = closes[j0 - 1]
            amp = (h0 - l0) / prev_c * 100
            if not (c0 < o0 and amp >= P2_AMP):
                continue
            for k in range(1, P2_ENGULF_WIN + 1):
                wk = wi + k
                if wk >= n_win:
                    break
                d1 = win[wk]
                j1 = fpos.get(d1)
                if j1 is None:
                    continue
                o1, h1, l1, c1 = arr[j1][1:5]
                if c1 > o1 and c1 > o0:
                    fired["engulf"].append({
                        "code": code, "name": names.get(code) or code, "date": d1,
                        "detail": "%s 板后 %s 高位大阴（振幅 %.1f%%），%d 天后实体反包" % (
                            lb.get((dprev, code)), _fmt(d0), amp, k),
                        "meta": {"lb": lb.get((dprev, code)), "dark": d0,
                                 "amp": round(amp, 1), "gap": k}})
                    break

        # ---------- P3 连板回均线反包 ----------
        for wi in range(n_win - 1):
            dstart = win[wi]
            if lb.get((dstart, code), 0) < P3_MIN_LB:
                continue
            j0 = fpos.get(dstart)
            if j0 is None:
                continue
            hit = None
            for k in range(1, P3_TOUCH_WIN + 1):
                wk = wi + k
                if wk >= n_win:
                    break
                d = win[wk]
                j = fpos.get(d)
                if j is None:
                    continue
                ma = _ma10(closes, j)
                if ma is None:
                    continue
                o, h, l, c = arr[j][1:5]
                if l <= ma * P3_BAND_UP and c >= ma * P3_BAND_DN:
                    hit = (d, j, ma, round((l / ma - 1) * 100, 1), k)
                    break
            if not hit:
                continue
            hd, hj, ma, dev, hk = hit
            hi = wi + hk
            done = False
            for k in range(1, P3_ENGULF_WIN + 1):
                wk2 = hi + k
                if wk2 >= n_win:
                    break
                d1 = win[wk2]
                j1 = fpos.get(d1)
                if j1 is None or j1 == 0:
                    continue
                o1, h1, l1, c1 = arr[j1][1:5]
                ph = arr[j1 - 1][2]
                if c1 > o1 and c1 > ph:
                    fired["mareb"].append({
                        "code": code, "name": names.get(code) or code, "date": d1,
                        "detail": "%s 连板后 %d 天回踩 MA10（低点距均线 %+.1f%%），%d 天后阳线反包" % (
                            _fmt(dstart), hk, dev, k),
                        "meta": {"start": dstart, "touch": hd, "ma_dev": dev, "gap": k}})
                    done = True
                    break
            if not done and hi + P3_ENGULF_WIN >= n_win:
                jd = fpos.get(today)
                ma_now = _ma10(closes, jd)
                if jd is not None and ma_now and arr[jd][4] >= ma_now * P3_KEEP:
                    watch["mareb"].append({
                        "code": code, "name": names.get(code) or code, "date": hd,
                        "detail": "%s 连板后第 %d 天回踩 MA10（低点距均线 %+.1f%%），未反包未破位，等待反包/金叉" % (
                            _fmt(dstart), hk, dev),
                        "meta": {"start": dstart, "touch": hd, "ma_dev": dev}})

    for k in fired:
        fired[k].sort(key=lambda e: e["date"], reverse=True)
        del fired[k][MAX_FIRED:]
    for k in watch:
        watch[k].sort(key=lambda e: e["date"], reverse=True)
        del watch[k][MAX_WATCH:]

    counts = {}
    today_events = []
    for k in ("refirst", "engulf", "mareb"):
        ft = [e for e in fired.get(k, []) if e["date"] == today]
        today_events.extend(dict(e, key=k) for e in ft)
        counts[k] = {"fired_today": len(ft), "fired": len(fired.get(k, [])),
                     "watching": len(watch.get(k, []))}
    today_events.sort(key=lambda e: e["key"])
    return {"window": {"start": win[0], "end": today}, "today": today,
            "counts": counts, "today_events": today_events,
            "fired": fired, "watching": watch}
