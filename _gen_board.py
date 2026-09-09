#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股行情看板 · P1 短线看板生成器
读 data/board.db → 生成单文件静态 HTML（情绪面板 + 连板梯队 + 多条件筛选 + 历史日切换）
用法：
    python _gen_board.py                # 渲染所有已采集日期
    python _gen_board.py --date=20260818  # 只渲染指定日期
输出：board.html
"""
import argparse
import json
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "board.db")
OUT = os.path.join(BASE, "board.html")

IDX = {
    "sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
    "sh000688": "科创50", "sh000300": "沪深300",
}


def analyze_lowpos(conn):
    """低位潜力股：位置低(距52周高回落≥25%) + 近期活跃(20日涨停/放量) + 基本面(ROE>0) + 题材热度
    全用现有数据（kline/pool_daily/fin_hist/value_hist），按行业分组输出"""
    # 行业映射（近 10 日涨停/炸板池）+ 题材热度（近 5 日行业涨停家数）
    ind_map = {}
    ind_heat = {}
    dates_all = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM collect_log WHERE status='ok' ORDER BY date DESC LIMIT 30")]
    for d in dates_all[:10]:
        for c, n, j in conn.execute(
                "SELECT code, name, json_extract(data_json,'$.所属行业') FROM pool_daily "
                "WHERE date=? AND pool_type IN ('zt','zb')", (d,)):
            if j:
                ind_map.setdefault(c, j)
    for d in dates_all[:5]:
        for j in conn.execute(
                "SELECT DISTINCT json_extract(data_json,'$.所属行业') FROM pool_daily "
                "WHERE date=? AND pool_type='zt'", (d,)):
            ind = j[0]
            if ind:
                ind_heat[ind] = ind_heat.get(ind, 0) + 1
    # 近 20 日涨停史
    zt_days = {}
    for d in dates_all[:20]:
        for c, in conn.execute(
                "SELECT code FROM pool_daily WHERE date=? AND pool_type='zt'", (d,)):
            zt_days.setdefault(c, []).append(d)

    names = {}
    for c, n in conn.execute("SELECT code, name FROM trend_cand ORDER BY date DESC"):
        names.setdefault(c, n)
    for d in dates_all[:3]:
        for c, n in conn.execute("SELECT code, name FROM pool_daily WHERE date=?", (d,)):
            names.setdefault(c, n)

    cands = []
    for code, in conn.execute("SELECT DISTINCT code FROM kline"):
        rows = conn.execute(
            "SELECT close, volume FROM kline WHERE code=? ORDER BY date", (code,)).fetchall()
        if len(rows) < 130:
            continue
        closes = [r[0] for r in rows]
        vols = [r[1] for r in rows]
        cur = closes[-1]
        high52 = max(closes)
        dist52 = (cur / high52 - 1) * 100
        if dist52 > -15:
            continue  # 距高点回落不足，不算低位
        # 近期活跃：20 日有涨停 或 近 10 日放量（量比 > 2）
        zt20 = bool(zt_days.get(code))
        vol_ratio = max(vols[-10:]) / (sum(vols[-30:-10]) / 20) if len(vols) >= 30 else 1
        active = zt20 or vol_ratio > 2
        if not active:
            continue
        # 基本面（可选：有财务数据加分，无则跳过——kline 池大部分无 fin_hist）
        roe_v = None
        roe = conn.execute(
            "SELECT roe FROM fin_hist WHERE code=? AND roe IS NOT NULL ORDER BY date DESC LIMIT 1",
            (code,)).fetchone()
        if roe:
            roe_v = roe[0]
        mv_v = None
        mv = conn.execute(
            "SELECT total_mv FROM value_hist WHERE code=? ORDER BY date DESC LIMIT 1",
            (code,)).fetchone()
        if mv and mv[0]:
            mv_v = mv[0]
            if mv_v < 5e9:
                continue  # 市值 < 50 亿排除（仅当有市值数据时）
        # 潜力评分 10
        score = 0
        if -40 <= dist52 <= -15:
            score += 3  # 适中低位有空间
        else:
            score += 1  # 深跌（价值陷阱风险）
        if zt20:
            score += 2
        if vol_ratio > 2:
            score += 1
        if roe_v is not None:
            if roe_v >= 10:
                score += 2
            elif roe_v > 0:
                score += 1
        ind = ind_map.get(code, "其他")
        score += min(3, ind_heat.get(ind, 0))
        cands.append({
            "code": code, "名称": names.get(code, code), "ind": ind,
            "dist52": round(dist52, 1), "score": score,
            "roe": round(roe_v, 1) if roe_v is not None else None,
            "mv": round(mv_v / 1e8, 0) if mv_v else None,
            "zt_days": len(zt_days.get(code, [])),
            "vol": round(vol_ratio, 1),
        })
    cands.sort(key=lambda x: -x["score"])
    # 按行业分组
    groups = {}
    for c in cands:
        groups.setdefault(c["ind"], []).append(c)
    out = []
    for ind, lst in sorted(groups.items(), key=lambda kv: -max(x["score"] for x in kv[1])):
        out.append({"ind": ind, "heat": ind_heat.get(ind, 0),
                    "stocks": lst[:6], "n": len(lst)})
    return {"groups": out[:12], "total": len(cands)}


def analyze_trend(conn):
    """P4 中长线趋势分析：指数状态 + 趋势池（均线多头/新高/RS/回踩/突破）+ 评分"""
    # 1) 指数趋势状态
    idx = {}
    for code, name in IDX.items():
        rows = conn.execute(
            "SELECT date, close FROM idx_daily WHERE code=? ORDER BY date", (code,)).fetchall()
        if len(rows) < 60:
            continue
        closes = [r[1] for r in rows]
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60
        ma120 = sum(closes[-120:]) / 120 if len(closes) >= 120 else None
        if ma20 > ma60 and (ma120 is None or ma60 > ma120):
            st = "多头"
        elif ma20 < ma60 and (ma120 is None or ma60 < ma120):
            st = "空头"
        else:
            st = "震荡"
        idx[name] = {
            "code": code, "close": round(closes[-1], 2),
            "pct20": round((closes[-1] / closes[-21] - 1) * 100, 2) if len(closes) >= 21 else 0,
            "ma20": round(ma20, 2), "ma60": round(ma60, 2),
            "ma120": round(ma120, 2) if ma120 else None, "status": st,
        }

    # 2) 趋势池（基准 = 沪深300 20日涨幅）
    bench20 = idx.get("沪深300", {}).get("pct20", 0)
    names = {}
    for c, n in conn.execute("SELECT code, name FROM trend_cand ORDER BY date DESC"):
        names.setdefault(c, n)
    for d in [r[0] for r in conn.execute(
            "SELECT DISTINCT date FROM collect_log WHERE status='ok' ORDER BY date DESC LIMIT 3")]:
        for c, n in conn.execute(
                "SELECT code, name FROM pool_daily WHERE date=?", (d,)):
            names.setdefault(c, n)

    pool = []
    for code, in conn.execute("SELECT DISTINCT code FROM kline"):
        rows = conn.execute(
            "SELECT date, high, low, close, volume FROM kline WHERE code=? ORDER BY date", (code,)).fetchall()
        if len(rows) < 70:
            continue
        closes = [r[3] for r in rows]
        vols = [r[4] for r in rows]
        cur = closes[-1]
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60
        ma120 = sum(closes[-120:]) / 120 if len(closes) >= 120 else ma60
        bull = ma20 > ma60 > ma120
        half_bull = ma20 > ma60
        high60 = cur >= max(closes[-60:]) * 0.995
        high52 = max(closes)
        dist52 = (cur / high52 - 1) * 100
        pct20 = (cur / closes[-21] - 1) * 100 if len(closes) >= 21 else 0
        rs = round(pct20 - bench20, 2)
        pullback = bull and (abs(cur / ma10 - 1) <= 0.03 or abs(cur / ma20 - 1) <= 0.03)
        prev_high = max(closes[-21:-1]) if len(closes) >= 21 else cur
        vol_avg5 = sum(vols[-6:-1]) / 5 if len(vols) >= 6 else 1
        breakout = cur > prev_high and vols[-1] > vol_avg5 * 1.5

        score = 0
        if bull:
            score += 4
        elif half_bull:
            score += 2
        if high60:
            score += 2
        if rs > 0:
            score += 2
        if dist52 > -15:
            score += 2
        lv = "强" if score >= 9 else ("中" if score >= 6 else "弱")

        pool.append({
            "code": code, "名称": names.get(code, code),
            "close": round(cur, 2), "pct20": round(pct20, 2), "rs": rs,
            "dist52": round(dist52, 2), "bull": bull, "high60": high60,
            "pullback": pullback, "breakout": breakout, "score": score,
            "lv": lv, "ma20": round(ma20, 2), "ma60": round(ma60, 2),
        })
    pool.sort(key=lambda x: -x["score"])
    return {"idx": idx, "pool": pool, "bench20": bench20}


def load_dates(conn):
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM collect_log WHERE status='ok' ORDER BY date")]


def load_day(conn, d):
    """读某日三类池 + 广度，返回原始 dict 列表"""
    pools = {}
    for pt in ("zt", "dt", "zb"):
        rows = conn.execute(
            "SELECT data_json FROM pool_daily WHERE date=? AND pool_type=?", (d, pt)).fetchall()
        pools[pt] = [json.loads(r[0]) for r in rows]
    b = conn.execute(
        "SELECT up,down,flat,limit_up,limit_down,total,activity,data_json "
        "FROM breadth WHERE date=?", (d,)).fetchone()
    breadth = None
    if b:
        raw = json.loads(b[7]) if b[7] else {}
        breadth = {
            "up": b[0], "down": b[1], "flat": b[2],
            "limit_up": b[3], "limit_down": b[4], "total": b[5],
            "activity": b[6] or "",
            "real_zt": raw.get("真实涨停"), "real_dt": raw.get("真实跌停"),
        }
    return pools, breadth


def sentiment(pools, breadth):
    """情绪规则引擎 v0：涨停/跌停/炸板率/连板高度 → 情绪标签"""
    zt_n = len(pools["zt"])
    dt_n = len(pools["dt"])
    zb_n = len(pools["zb"])
    lianbans = [int(r.get("连板数") or 0) for r in pools["zt"]]
    max_lb = max(lianbans) if lianbans else 0
    zbrate = round(zb_n / (zt_n + zb_n) * 100, 1) if (zt_n + zb_n) else 0
    top = [r for r in pools["zt"] if int(r.get("连板数") or 0) == max_lb] if max_lb >= 3 else []

    if dt_n >= 20 or (zt_n <= 30 and zbrate >= 50):
        tag, cls = "全面退潮", "danger"
    elif zbrate >= 35 or dt_n >= 10:
        tag, cls = "局部退潮", "warn"
    elif zt_n >= 80 and zbrate < 25 and max_lb >= 4:
        tag, cls = "情绪加强", "good"
    elif zt_n >= 50 and zbrate < 30 and max_lb >= 3:
        tag, cls = "情绪修复", "good"
    else:
        tag, cls = "震荡混沌", "flat"

    return {
        "zt": zt_n, "dt": dt_n, "zb": zb_n, "zbrate": zbrate, "max_lb": max_lb,
        "tag": tag, "tag_cls": cls,
        "top": [{"名称": r.get("名称"), "code": r.get("代码"),
                 "lb": int(r.get("连板数") or 0), "ztstat": r.get("涨停统计")} for r in top],
    }


def analyze_stocks(pools, sent=None):
    """个股延续性评分 + 次日策略（规则引擎 v1，情绪系数 v2）
    四维评分（各 0-3 分）：封板强度 / 封板资金 / 换手质量 / 位置 / 地位
    总分 15：强(≥11) / 中(8-10.5) / 弱(<8)；退潮/震荡期收紧阈值（回测复盘优化）"""
    zt = pools["zt"]
    strict = sent is not None and sent.get("tag") in ("全面退潮", "局部退潮", "震荡混沌")
    th_strong = 12.5 if strict else 11
    th_mid = 9 if strict else 8
    # 行业地位：板块内按连板数+封板资金排序取前 1/3
    ind_count = {}
    for r in zt:
        ind = r.get("所属行业") or "其他"
        ind_count[ind] = ind_count.get(ind, 0) + 1
    for r in zt:
        ind = r.get("所属行业") or "其他"
        rank = sorted([x for x in zt if (x.get("所属行业") or "其他") == ind],
                      key=lambda x: (int(x.get("连板数") or 0), float(x.get("封板资金") or 0)), reverse=True)
        pos = rank.index(r) + 1
        r["_ind_count"] = ind_count[ind]
        r["_ind_rank"] = pos

    for r in zt:
        t = str(r.get("首次封板时间") or "150000")
        hm = int(t[:2]) * 60 + int(t[2:4])
        if hm <= 600:
            seal = 3
        elif hm <= 870:
            seal = 2
        else:
            seal = 1
        zb = int(r.get("炸板次数") or 0)
        if zb == 0:
            seal += 1
        elif zb >= 3:
            seal -= 1
        seal = max(1, min(4, seal))

        fund = float(r.get("封板资金") or 0)
        if fund >= 100000000:
            f_score = 3
        elif fund >= 30000000:
            f_score = 2
        else:
            f_score = 1

        turn = float(r.get("换手率") or 0)
        if 3 <= turn <= 20:
            t_score = 3
        elif 1 <= turn < 3:
            t_score = 2
        else:
            t_score = 1

        lb = int(r.get("连板数") or 0)
        if lb <= 1:
            p_score = 3
        elif lb == 2:
            p_score = 2
        elif lb == 3:
            p_score = 1.5
        else:
            p_score = 1

        if r["_ind_count"] >= 3 and r["_ind_rank"] <= 2:
            s_score = 3
        elif r["_ind_rank"] <= 3:
            s_score = 2
        else:
            s_score = 1

        total = seal + f_score + t_score + p_score + s_score
        if total >= th_strong:
            level, level_cls = "强", "lv-strong"
        elif total >= th_mid:
            level, level_cls = "中", "lv-mid"
        else:
            level, level_cls = "弱", "lv-weak"

        # 次日策略（分档）
        if level == "强":
            if seal >= 4:
                strat = "竞价高开≤5%且量能温和，可关注分歧接力；高开>7%防兑现"
            else:
                strat = "封板结构良好，回踩不破分时均价可低吸；冲高兑现部分"
        elif level == "中":
            strat = "分歧观察为主：高开冲高兑现，回踩不破涨停价-3%可低吸试错"
        else:
            strat = "以兑现/减仓为主：弱反抽离场，不追高"
        risk = "跌破前收-3%（竞价大幅低开）离场观望，仓位不超 1/3"

        r["_analysis"] = {
            "total": round(total, 1), "level": level, "level_cls": level_cls,
            "seal": seal, "fund": f_score, "turn": t_score, "pos": p_score, "status": s_score,
            "strat": strat, "risk": risk,
        }
        ind = r.get("所属行业") or "其他"
        r["_reason"] = f"{ind}·{ind_count[ind]}家"
        r["_attr"] = _attribute_reason(r, ind_count[ind])


def _attribute_reason(r, ind_cnt):
    """P6-A 涨停四维归因：题材/资金/技术/消息 → 归因向量 + 主标签"""
    topic = min(50, int(ind_cnt or 1) * 8)
    if (r.get("_ind_rank") or 9) <= 2:
        topic += 10  # 板块内前 2 = 卡位
    if int(r.get("连板数") or 0) >= 2:
        topic += 8  # 有梯队延续 = 题材属性增强
    fund = float(r.get("封板资金") or 0)
    money = 10
    if fund >= 100000000:
        money += 20
    elif fund >= 30000000:
        money += 10
    turn = float(r.get("换手率") or 0)
    if 3 <= turn <= 20:
        money += 10  # 健康换手
    tech = 15 if int(r.get("连板数") or 0) <= 1 else 0  # 低位首板
    if int(r.get("炸板次数") or 0) >= 3:
        tech -= 5
    # 消息分：仅当题材/资金/技术均弱时占主导，且设上限 30（需公告验证，避免虚高）
    msg = min(30, max(0, 100 - topic - money - tech))
    s = topic + money + tech + msg
    parts = {"题材": topic, "资金": money, "技术": tech, "消息": msg}
    main = max(parts, key=parts.get)
    return {"topic": round(topic / s * 100), "money": round(money / s * 100),
            "tech": round(tech / s * 100), "msg": round(msg / s * 100), "main": main}


def analyze_themes(pools, sent):
    """题材聚类 + 阶段判断 + 高低切 v0（基于行业聚合）"""
    zt = pools["zt"]
    groups = {}
    for r in zt:
        ind = r.get("所属行业") or "其他"
        groups.setdefault(ind, []).append(r)
    themes = []
    for name, arr in groups.items():
        lbs = [int(x.get("连板数") or 0) for x in arr]
        max_lb = max(lbs)
        total_seal = sum(float(x.get("封板资金") or 0) for x in arr)
        leader = max(arr, key=lambda x: (int(x.get("连板数") or 0), float(x.get("封板资金") or 0)))
        # 阶段判断 v0
        if max_lb >= 4:
            stage, cls = "高潮", "danger"
        elif max_lb >= 3:
            stage, cls = "发酵", "warn"
        elif max_lb == 2 or (len(arr) >= 8):
            stage, cls = "启动扩散", "good"
        elif len(arr) >= 4:
            stage, cls = "启动", "good"
        else:
            stage, cls = "试盘", "flat"
        # 高低切标签 v0：高位（3板+）vs 低位新启动（全首板且家数足）
        if max_lb >= 3:
            hl = "高位区"
            hl_cls = "warn"
        elif max_lb == 1 and len(arr) >= 5:
            hl = "低位启动"
            hl_cls = "good"
        else:
            hl = ""
            hl_cls = ""
        themes.append({
            "名称": name, "count": len(arr), "max_lb": max_lb,
            "lb_names": "/".join(str(x) for x in sorted(set(lbs), reverse=True)),
            "total_seal": round(total_seal / 100000000, 2),
            "leader": {"名称": leader.get("名称"), "code": leader.get("代码"),
                       "lb": int(leader.get("连板数") or 0)},
            "stage": stage, "stage_cls": cls,
            "hl": hl, "hl_cls": hl_cls,
        })
    themes.sort(key=lambda t: (t["max_lb"], t["count"]), reverse=True)

    # 高低切结论 v0
    high = [t for t in themes if t["hl"] == "高位区"]
    low = [t for t in themes if t["hl"] == "低位启动"]
    conclusion = None
    if high or low:
        parts = []
        if high:
            parts.append("高位区: " + "、".join(t["名称"] for t in high[:4]) + " —— 注意分歧兑现风险")
        if low:
            parts.append("低位启动: " + "、".join(t["名称"] for t in low[:4]) + " —— 观察承接与扩散")
        conclusion = {
            "text": "；".join(parts),
            "watch": "明日核心变量: 高位龙头分歧是否扩散、低位新题材能否走出首板晋级",
        }
    return themes, conclusion


def load_ext(conn, d):
    """加载 P3 扩展数据：龙虎榜 / 板块资金流 / 昨日涨停跟踪"""
    ext = {"lhb": [], "fund": [], "prev": []}
    rows = conn.execute("SELECT data_json FROM lhb WHERE date=?", (d,)).fetchall()
    ext["lhb"] = [json.loads(r[0]) for r in rows]
    rows = conn.execute("SELECT data_json FROM fund_flow WHERE date=?", (d,)).fetchall()
    for r in rows:
        arr = json.loads(r[0])
        if isinstance(arr, list):
            ext["fund"] = arr
    rows = conn.execute("SELECT data_json FROM prev_zt WHERE date=?", (d,)).fetchall()
    ext["prev"] = [json.loads(r[0]) for r in rows]
    return ext


def analyze_ext(ext, pools):
    """P3 分析：龙虎榜 / 板块资金流 / 昨日涨停跟踪（复盘闭环）"""
    lhb = ext.get("lhb") or []
    fund = ext.get("fund") or []
    prev = ext.get("prev") or []

    def _f(r, k):
        try:
            return float(r.get(k) or 0)
        except (TypeError, ValueError):
            return 0

    out = {"lhb_top_buy": [], "lhb_top_sell": [], "lhb_zt": [], "fund_in": [], "fund_out": [], "prev": None}
    if lhb:
        s = sorted(lhb, key=lambda x: -_f(x, "龙虎榜净买额"))
        # 去重：同代码多次上榜（不同原因）取净买额绝对值最大的一条
        seen = {}
        for r in s:
            code = r.get("代码")
            if code not in seen or abs(_f(r, "龙虎榜净买额")) > abs(_f(seen[code], "龙虎榜净买额")):
                seen[code] = r
        uniq = list(seen.values())
        out["lhb_top_buy"] = sorted(uniq, key=lambda x: -_f(x, "龙虎榜净买额"))[:10]
        out["lhb_top_sell"] = sorted(uniq, key=lambda x: _f(x, "龙虎榜净买额"))[:5]
        zt_codes = {r.get("代码") for r in pools["zt"]}
        out["lhb_zt"] = [r for r in uniq if r.get("代码") in zt_codes][:10]
    if fund:
        out["fund_in"] = sorted(fund, key=lambda x: -_f(x, "净额"))[:8]
        out["fund_out"] = sorted(fund, key=lambda x: _f(x, "净额"))[:5]
    if prev:
        jn = []
        db = []
        for r in prev:
            px = _f(r, "最新价")
            ztpx = _f(r, "涨停价")
            if ztpx > 0 and abs(px - ztpx) / ztpx < 0.001:
                jn.append(r)
            else:
                db.append(r)
        avg = sum(_f(r, "涨跌幅") for r in prev) / len(prev) if prev else 0
        out["prev"] = {
            "total": len(prev), "jn": len(jn), "db": len(db),
            "jn_rate": round(len(jn) / len(prev) * 100, 1) if prev else 0,
            "avg_pct": round(avg, 2),
            "jn_list": sorted(jn, key=lambda x: -_f(x, "涨跌幅"))[:12],
            "db_list": sorted(db, key=lambda x: -_f(x, "涨跌幅"))[:12],
        }
    return out


def analyze_value(conn):
    """P5 长线价值：估值分位（5年 PE TTM/PB）+ 巴式体检评分（价值池 + 蓝筹池双池）"""
    def _load(fn):
        wl = os.path.join(BASE, fn)
        if os.path.exists(wl):
            try:
                return json.load(open(wl, encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _calc(watch, is_bluechip, is_growth):
        pool = []
        for code, name in watch.items():
            vrows = conn.execute(
                "SELECT date, close, pe_ttm, pb, total_mv FROM value_hist WHERE code=? "
                "AND pe_ttm IS NOT NULL ORDER BY date", (code,)).fetchall()
            if len(vrows) < 60:
                continue
            look = vrows[-1250:]
            pes = [r[2] for r in look if r[2] and r[2] > 0]
            pbs = [r[3] for r in look if r[3] and r[3] > 0]
            cur_pe, cur_pb, cur_close, cur_mv = vrows[-1][2], vrows[-1][3], vrows[-1][1], vrows[-1][4]
            if not pes or not pbs:
                continue
            pe_pct = round(sum(1 for x in pes if x < cur_pe) / len(pes) * 100)
            pb_pct = round(sum(1 for x in pbs if x < cur_pb) / len(pbs) * 100)
            if pe_pct < 30:
                val_tag, val_cls = "便宜", "good"
            elif pe_pct < 60:
                val_tag, val_cls = "合理", "flat"
            else:
                val_tag, val_cls = "偏贵", "warn"

            frows = conn.execute(
                "SELECT roe, profit_margin, debt_ratio, cf_roa, rev_growth FROM fin_hist "
                "WHERE code=? AND roe IS NOT NULL ORDER BY date", (code,)).fetchall()
            f = frows[-1] if frows else None
            roes = [r[0] for r in frows[-8:]] if frows else []
            roe = f[0] if f else None
            debt = f[2] if f else None
            cf = f[3] if f else None
            rev_g = f[4] if f else None
            roe_avg = round(sum(roes) / len(roes), 1) if roes else None
            roe_use = roe_avg if roe_avg is not None else roe

            score = 0
            if pe_pct < 30:
                score += 3
            elif pe_pct < 50:
                score += 2
            else:
                score += 1
            if roe_use is not None:
                if roe_use >= 15:
                    score += 3
                elif roe_use >= 10:
                    score += 2
                else:
                    score += 1
            if is_bluechip:
                if cur_mv and cur_mv >= 2e11:
                    score += 2
                elif cur_mv and cur_mv >= 1e11:
                    score += 1
                if debt is not None:
                    score += 1 if debt < 60 else 0
            elif is_growth:
                # 科技成长侧重：成长（营收/净利增速）2 + 负债率 2
                g = 0
                if rev_g is not None and rev_g > 10:
                    g += 1
                if frows and (f[4] or 0) and f[4] > 10:
                    g += 1
                score += g
                if debt is not None:
                    score += 2 if debt < 60 else 1
            else:
                if debt is not None:
                    score += 2 if debt < 50 else 1
                if rev_g is not None and rev_g > 0:
                    score += 2
                elif cf is not None and cf > 0:
                    score += 1
            lv = "优" if score >= 8 else ("良" if score >= 6 else "一般")
            lv_cls = "lv-strong" if lv == "优" else ("lv-mid" if lv == "良" else "lv-weak")

            pool.append({
                "code": code, "名称": name, "close": round(cur_close, 2),
                "pe_ttm": round(cur_pe, 1) if cur_pe else None,
                "pb": round(cur_pb, 2) if cur_pb else None,
                "pe_pct": pe_pct, "pb_pct": pb_pct,
                "val_tag": val_tag, "val_cls": val_cls,
                "roe": round(roe_use, 1) if roe_use is not None else None,
                "roe_avg": roe_avg, "debt": round(debt, 1) if debt is not None else None,
                "cf_roa": round(cf, 1) if cf is not None else None,
                "rev_g": round(rev_g, 1) if rev_g is not None else None,
                "mv": round(cur_mv / 1e8, 0) if cur_mv else None,  # 亿元
                "score": score, "lv": lv, "lv_cls": lv_cls,
            })
        pool.sort(key=lambda x: -x["score"])
        return pool

    return {"pool": _calc(_load("value_watchlist.json"), False, False),
            "bluechip": _calc(_load("bluechip_watchlist.json"), True, False),
            "growth": _calc(_load("growth_watchlist.json"), False, True)}


def analyze_seats(conn, date_str):
    """P6-A 龙虎榜席位解析：风格打标 + 净买方向 + 历史活跃度"""
    style_file = os.path.join(BASE, "seat_style.json")
    if not os.path.exists(style_file):
        return {"stocks": {}, "hot": [], "count": 0}
    style = json.load(open(style_file, encoding="utf-8"))
    hot = style.get("known_hot_money", [])
    retail = style.get("retail_channels", [])

    def tag(seat):
        if "机构专用" in seat:
            return "机构"
        if any(h in seat for h in hot):
            return "知名游资"
        if "量化" in seat:
            return "量化"
        if any(k in seat for k in retail):
            return "散户通道"
        if "深股通" in seat or "沪股通" in seat:
            return "北向"
        return "其他"

    rows = conn.execute(
        "SELECT code, seat, buy_amt, sell_amt, net FROM seat_daily WHERE date=? "
        "ORDER BY code", (date_str,)).fetchall()
    stocks = {}
    for code, seat, buy, sell, net in rows:
        seat = str(seat)
        key = (code, seat)
        item = stocks.setdefault(key, {
            "code": code, "seat": seat, "tag": tag(seat),
            "buy": 0, "sell": 0, "net": 0,
        })
        item["buy"] += buy if buy else 0
        item["sell"] += sell if sell else 0
        item["net"] += net if net else 0
    by_code = {}
    for (code, _seat), item in stocks.items():
        by_code.setdefault(code, []).append(item)
    # 席位历史活跃度（不含当日）+ 胜率画像（K 线算次日涨跌）
    hist = {}
    for code, seat, net, d in conn.execute(
            "SELECT code, seat, net, date FROM seat_daily WHERE date < ?", (date_str,)):
        s = str(seat)
        h = hist.setdefault(s, {"n": 0, "buy_n": 0, "win": 0, "avg": []})
        h["n"] += 1
        if net and net > 0:
            h["buy_n"] += 1
            # 次日涨跌：该股 d 后首个交易日收盘 vs d 日收盘
            nxt_r = conn.execute(
                "SELECT close FROM kline WHERE code=? AND date>? ORDER BY date LIMIT 1",
                (code, d)).fetchone()
            cur_r = conn.execute(
                "SELECT close FROM kline WHERE code=? AND date=?",
                (code, d)).fetchone()
            if nxt_r and cur_r and cur_r[0]:
                chg = (nxt_r[0] / cur_r[0] - 1) * 100
                if chg > 0:
                    h["win"] += 1
                h["avg"].append(chg)
    # 知名游资当日动向（买/卖双向，按金额绝对值排序）
    hot_act = []
    names = {r[0]: r[1] for r in conn.execute(
        "SELECT DISTINCT code, name FROM pool_daily WHERE date=? AND pool_type IN ('zt','dt')", (date_str,))}
    for c, n in conn.execute(
            "SELECT DISTINCT code, name FROM lhb WHERE date=?", (date_str,)):
        names.setdefault(c, n)  # 龙虎榜股名称兜底（非涨停/跌停的上榜股）
    for code, seats_l in by_code.items():
        for s in seats_l:
            if s["tag"] == "知名游资" and s["net"] != 0:
                h = hist.get(s["seat"], {"n": 0, "buy_n": 0, "win": 0, "avg": []})
                hot_act.append({
                    "seat": s["seat"], "code": code,
                    "名称": names.get(code, code), "net": s["net"],
                    "hist_n": h["n"],
                    "hist_win": round(h["win"] / h["buy_n"] * 100) if h["buy_n"] else None,
                })
    hot_act.sort(key=lambda x: -abs(x["net"]))
    return {"stocks": by_code, "hot": hot_act[:15], "count": len(rows)}


def analyze_movement(conn):
    """P6-B 异动监管监测：20日+100% / 30日+200% 阈值预警 + 监管清单叠加"""
    # 监管事件清单（人工/半自动维护）
    regs = {}
    reg_file = os.path.join(BASE, "reg_watch.json")
    if os.path.exists(reg_file):
        try:
            for ev in json.load(open(reg_file, encoding="utf-8")).get("events", []):
                c = str(ev.get("code", "")).strip()
                if c:
                    regs.setdefault(c, []).append(ev)
        except Exception:
            pass
    names = {}
    for c, n in conn.execute("SELECT code, name FROM trend_cand ORDER BY date DESC"):
        names.setdefault(c, n)
    for d in [r[0] for r in conn.execute(
            "SELECT DISTINCT date FROM collect_log WHERE status='ok' ORDER BY date DESC LIMIT 3")]:
        for c, n in conn.execute("SELECT code, name FROM pool_daily WHERE date=?", (d,)):
            names.setdefault(c, n)

    alerts = []
    for code, in conn.execute("SELECT DISTINCT code FROM kline"):
        rows = conn.execute(
            "SELECT close FROM kline WHERE code=? ORDER BY date", (code,)).fetchall()
        if len(rows) < 31:
            continue
        closes = [r[0] for r in rows]
        cur = closes[-1]
        if not closes[-21] or not closes[-31] or cur <= 0:
            continue
        g20 = round((cur / closes[-21] - 1) * 100, 1)
        g30 = round((cur / closes[-31] - 1) * 100, 1)
        level = None
        if g30 >= 200:
            level = "T2"
        elif g20 >= 100:
            level = "T1"
        elif g30 >= 180 or g20 >= 90:
            level = "T0"
        if not level:
            continue
        evs = regs.get(code, [])
        if evs:
            risk = "监管叠加"
            risk_cls = "danger"
        elif level == "T2":
            risk = "高"
            risk_cls = "danger"
        elif level == "T1":
            risk = "中"
            risk_cls = "warn"
        else:
            risk = "观察"
            risk_cls = "flat"
        alerts.append({
            "code": code, "名称": names.get(code, code),
            "g20": g20, "g30": g30, "level": level, "risk": risk,
            "risk_cls": risk_cls,
            "regs": [{"type": e.get("type", ""), "date": e.get("date", ""),
                      "note": e.get("note", "")} for e in evs],
        })
    alerts.sort(key=lambda x: -max(x["g20"], x["g30"]))

    # 风险仪表
    n_hot = sum(1 for a in alerts if a["level"] in ("T1", "T2"))
    n_reg = sum(1 for a in alerts if a["risk_cls"] == "danger")
    if n_hot >= 8 or n_reg >= 3:
        gauge = {"text": "异动密集/监管叠加，警惕情绪过热与退潮加速", "cls": "danger"}
    elif n_hot >= 3:
        gauge = {"text": "存在高位异动标的，注意兑现风险", "cls": "warn"}
    else:
        gauge = {"text": "异动水平正常", "cls": "ok"}
    return {"alerts": alerts, "n_hot": n_hot, "n_reg": n_reg, "gauge": gauge}


def analyze_leaders(conn, d, pools, sent):
    """P6-C 总龙/情绪龙头标识：四维评分 + 历史累积推导 + 切换信号"""
    zt = pools["zt"]
    if not zt:
        return {"emo": None, "total": None, "signals": [], "score_list": []}
    ind_count = {}
    for r in zt:
        ind = r.get("所属行业") or "其他"
        ind_count[ind] = ind_count.get(ind, 0) + 1
    max_lb = max(int(r.get("连板数") or 0) for r in zt)

    scored = []
    for r in zt:
        lb = int(r.get("连板数") or 0)
        ind = r.get("所属行业") or "其他"
        # ① 连板高度 40
        h = round(lb / max_lb * 40, 1) if max_lb else 0
        # ② 市场辨识度 20（空间板 + 频繁涨停）
        dis = 10 if (lb == max_lb and max_lb >= 2) else 0
        stat = str(r.get("涨停统计") or "")
        if "/" in stat:
            try:
                a, b = stat.split("/")
                if int(a) > int(b):
                    dis += 10
            except ValueError:
                pass
        # ③ 资金号召力 20
        fund = float(r.get("封板资金") or 0)
        money = 10 if fund >= 100000000 else (6 if fund >= 30000000 else 3)
        t = str(r.get("首次封板时间") or "150000")
        hm = int(t[:2]) * 60 + int(t[2:4])
        money += 10 if hm <= 600 else 0
        # ④ 带动效应 20（行业家数 + 连板跟随）
        drive = 10 if ind_count[ind] >= 5 else (6 if ind_count[ind] >= 3 else (3 if ind_count[ind] >= 2 else 0))
        follow = 10 if any(x is not r and x.get("所属行业") == ind
                           and int(x.get("连板数") or 0) >= 2 for x in zt) else 0
        total = round(min(100, h + dis + money + drive + follow), 1)
        scored.append({
            "code": r.get("代码"), "名称": r.get("名称"), "lb": lb, "ind": ind,
            "score": total, "h": h, "dis": dis, "money": money,
            "drive": drive, "follow": follow,
        })
    scored.sort(key=lambda x: (-x["score"], -x["lb"]))
    emo = scored[0]

    # 总龙头：近 5 日累计连板强度最高（周期核心标杆）
    acc = {}
    for dd in [r[0] for r in conn.execute(
            "SELECT DISTINCT date FROM collect_log WHERE status='ok' AND date<=? "
            "ORDER BY date DESC LIMIT 5", (d,))]:
        for c, n, j in conn.execute(
                "SELECT code, name, json_extract(data_json,'$.连板数') FROM pool_daily "
                "WHERE date=? AND pool_type='zt'", (dd,)):
            lbv = max(1, int(j or 1))
            a = acc.setdefault(c, {"名称": n, "acc": 0, "days": 0})
            a["acc"] += lbv
            a["days"] += 1
    total = None
    if acc:
        top_code = max(acc, key=lambda c: (acc[c]["acc"], acc[c]["days"]))
        top = acc[top_code]
        today_zt = {r.get("代码") for r in zt}
        total = {
            "code": top_code, "名称": top["名称"],
            "acc": top["acc"], "days": top["days"],
            "today": top_code in today_zt,
        }

    # 切换信号（对比昨日）
    signals = []
    prev_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM collect_log WHERE status='ok' AND date<? "
        "ORDER BY date DESC LIMIT 1", (d,))]
    if prev_dates:
        pd = prev_dates[0]
        prev_zt = conn.execute(
            "SELECT code, name, json_extract(data_json,'$.连板数') FROM pool_daily "
            "WHERE date=? AND pool_type='zt'", (pd,)).fetchall()
        if prev_zt:
            pmax = max(int(j or 1) for _, _, j in prev_zt)
            prev_top = [x for x in prev_zt if int(x[2] or 1) == pmax][0]
            today_codes = {r.get("代码") for r in zt}
            if total and prev_top[0] == total["code"] and not total["today"]:
                signals.append({"cls": "danger", "text": f"总龙头 {total['名称']} 今日断板 —— 周期顶部信号，警惕退潮"})
            elif prev_top[0] != total["code"] and total and total["today"]:
                signals.append({"cls": "good", "text": f"新王登基：总龙头更替为 {total['名称']}（近5日累计强度最高）"})
            if prev_top[0] != emo["code"]:
                signals.append({"cls": "warn", "text": f"情绪龙头切换：{prev_top[1]} → {emo['名称']}（分歧转一致/资金轮动）"})
    if not signals and emo:
        signals.append({"cls": "ok", "text": f"龙头结构稳定：总龙 {total['名称'] if total else '-'} · 情绪龙 {emo['名称']}（{emo['lb']}板）"})

    return {"emo": emo, "total": total, "signals": signals[:4], "score_list": scored[:6]}


def analyze_dragons(pools):
    """P6-D 潜龙识别：五维评分（量价3/题材2/梯队2/承接2/分歧转一致1）
    排除：一字板（换手<1）、空间板（已为龙头）。评分 ≥6 进潜龙候选池。"""
    zt = pools["zt"]
    if not zt:
        return {"pool": []}
    ind_count = {}
    for r in zt:
        ind = r.get("所属行业") or "其他"
        ind_count[ind] = ind_count.get(ind, 0) + 1
    max_lb = max(int(r.get("连板数") or 0) for r in zt)

    cands = []
    for r in zt:
        lb = int(r.get("连板数") or 0)
        ind = r.get("所属行业") or "其他"
        turn = float(r.get("换手率") or 0)
        fund = float(r.get("封板资金") or 0)
        zb = int(r.get("炸板次数") or 0)
        if lb >= max_lb or lb > 3:
            continue  # 空间板/高位板排除
        if turn < 1:
            continue  # 一字板排除（无分歧转一致特征）
        # ① 量价结构健康度（0-3）
        v = 0
        if 3 <= turn <= 15:
            v += 1
        t = str(r.get("首次封板时间") or "150000")
        hm = int(t[:2]) * 60 + int(t[2:4])
        if hm <= 600:
            v += 1  # 早盘封板，资金坚决
        if zb == 0:
            v += 1  # 干净板
        # ② 题材新颖性与空间（0-2）：启动扩散期最佳（3-8 家），高潮排除
        if 3 <= ind_count[ind] <= 8:
            s2 = 2
        elif ind_count[ind] <= 2:
            s2 = 1
        else:
            s2 = 0
        # ③ 连板梯队位置（0-2）：2 板卡位最佳
        s3 = 2 if lb == 2 else (1 if lb == 1 else 0)
        # ④ 资金承接（0-2）
        s4 = 2 if fund >= 100000000 else (1 if fund >= 30000000 else 0)
        # ⑤ 分歧转一致（0-1）：炸板回封 = 直接信号；高换手充分换手
        s5 = 1 if (1 <= zb <= 3) else (1 if 10 <= turn <= 20 else 0)
        score = v + s2 + s3 + s4 + s5
        if score < 6:
            continue
        cands.append({
            "code": r.get("代码"), "名称": r.get("名称"), "lb": lb, "ind": ind,
            "score": score, "v": v, "s2": s2, "s3": s3, "s4": s4, "s5": s5,
            "turn": round(turn, 1), "fund": fund, "zb": zb,
        })
    cands.sort(key=lambda x: (-x["score"], -x["lb"]))
    return {"pool": cands[:15]}


def analyze_promotion(days, dates):
    """板块晋级率：各板块首板率 / 一进二 / 二进三 / 三进四 + 同比昨日
    晋级归属 = 今日股票所在板块；比率 = 今日晋级数/昨日基数"""
    if len(dates) < 2:
        return []
    d, pd_ = dates[-1], dates[-2]
    day, pday = days[d], days[pd_]
    zt, pzt = day["pools"]["zt"], pday["pools"]["zt"]
    # 今日/昨日 代码→(连板数, 行业)
    cur = {r.get("代码"): (int(r.get("连板数") or 0), r.get("所属行业") or "其他") for r in zt}
    prv = {r.get("代码"): (int(r.get("连板数") or 0), r.get("所属行业") or "其他") for r in pzt}
    stats = {}  # ind -> dict

    def S(ind):
        return stats.setdefault(ind, {"n": 0, "fb": 0, "j12": 0, "j23": 0, "j34": 0,
                                      "p_fb": 0, "p_j12": 0, "p_j23": 0, "p_j34": 0,
                                      "p_base1": 0, "p_base2": 0, "p_base3": 0})

    # 今日：各板块涨停结构
    for code, (lb, ind) in cur.items():
        s = S(ind)
        s["n"] += 1
        if lb == 1:
            s["fb"] += 1
    # 昨日基数：昨日首板/2板/3板数（按今日归属板块计）
    for code, (lb, ind) in prv.items():
        if lb == 1:
            S(ind)["p_base1"] += 1
        elif lb == 2:
            S(ind)["p_base2"] += 1
        elif lb == 3:
            S(ind)["p_base3"] += 1
    # 晋级：昨日 lb=n 的股票今日 lb=n+1
    for code, (lb, ind) in prv.items():
        clb = cur.get(code, (0, None))[0]
        if clb and clb == lb + 1:
            s = S(ind)
            if lb == 1:
                s["j12"] += 1
            elif lb == 2:
                s["j23"] += 1
            elif lb == 3:
                s["j34"] += 1
    # 昨日的板块晋级率（同比用）：昨日 vs 前日
    prev_day_stats = {}
    if len(dates) >= 3:
        pp_d = dates[-3]
        pp_day = days[pp_d]
        pcur = {r.get("代码"): (int(r.get("连板数") or 0), r.get("所属行业") or "其他") for r in pday["pools"]["zt"]}
        pprv = {r.get("代码"): (int(r.get("连板数") or 0), r.get("所属行业") or "其他") for r in pp_day["pools"]["zt"]}
        for code, (lb, ind) in pprv.items():
            st = prev_day_stats.setdefault(ind, {"fb": 0, "n": 0, "j12": 0, "j23": 0, "j34": 0, "b1": 0, "b2": 0, "b3": 0})
            clb = pcur.get(code, (0, None))[0]
            st["n"] += 1
            if lb == 1:
                st["fb"] += 1
            if lb == 1:
                st["b1"] += 1
            elif lb == 2:
                st["b2"] += 1
            elif lb == 3:
                st["b3"] += 1
            if clb and clb == lb + 1:
                if lb == 1:
                    st["j12"] += 1
                elif lb == 2:
                    st["j23"] += 1
                elif lb == 3:
                    st["j34"] += 1
    # 装配输出
    out = []
    for ind, s in stats.items():
        fb_rate = round(s["fb"] / s["n"] * 100, 1) if s["n"] else 0
        j12_rate = round(s["j12"] / s["p_base1"] * 100, 1) if s["p_base1"] else None
        j23_rate = round(s["j23"] / s["p_base2"] * 100, 1) if s["p_base2"] else None
        j34_rate = round(s["j34"] / s["p_base3"] * 100, 1) if s["p_base3"] else None
        p = prev_day_stats.get(ind) or {}
        p_fb = round(p["fb"] / p["n"] * 100, 1) if p.get("n") else None
        p_j12 = round(p["j12"] / p["b1"] * 100, 1) if p.get("b1") else None
        p_j23 = round(p["j23"] / p["b2"] * 100, 1) if p.get("b2") else None
        p_j34 = round(p["j34"] / p["b3"] * 100, 1) if p.get("b3") else None
        out.append({
            "ind": ind, "n": s["n"], "fb": s["fb"], "fb_rate": fb_rate,
            "j12": s["j12"], "j12_rate": j12_rate, "j23": s["j23"], "j23_rate": j23_rate,
            "j34": s["j34"], "j34_rate": j34_rate,
            "fb_prev": p_fb, "j12_prev": p_j12, "j23_prev": p_j23, "j34_prev": p_j34,
        })
    out.sort(key=lambda x: (-x["n"], -(x["j12_rate"] or 0)))
    return out


def build_name_map(conn, dates):
    """股票名→代码 映射（资讯企业链接用），来源：涨停池/趋势候选/watchlist"""
    names = {}
    for d in (dates[-5:] if dates else []):
        for c, n in conn.execute(
                "SELECT code, name FROM pool_daily WHERE date=? AND pool_type='zt'", (d,)):
            if n and len(str(n)) >= 2:
                names.setdefault(str(n), c)
    for c, n in conn.execute("SELECT code, name FROM trend_cand"):
        if n and len(str(n)) >= 2:
            names.setdefault(str(n), c)
    for fn in ("value_watchlist.json", "bluechip_watchlist.json", "growth_watchlist.json"):
        wl = os.path.join(BASE, fn)
        if os.path.exists(wl):
            try:
                for c, n in json.load(open(wl, encoding="utf-8")).items():
                    names.setdefault(n, c)
            except Exception:
                pass
    return names


def load_news(conn, limit=200):
    """公告资讯：按发布时间倒序"""
    rows = conn.execute(
        "SELECT pub_time, title, summary, link, source, category, sentiment, reason "
        "FROM news ORDER BY pub_time DESC LIMIT ?", (limit,)).fetchall()
    return [{"pub_time": r[0] or "", "title": r[1], "summary": r[2] or "",
             "link": r[3] or "", "source": r[4], "category": r[5],
             "sentiment": r[6], "reason": r[7] or ""} for r in rows]


def analyze_screener(conn, days, dates, trend, value):
    """选股器：短线/中线/长线三模式，多维评分
    短线=技术面40+情绪面30+资金面30（涨停池+潜龙）
    中线=技术面40+基本面40+量价20（趋势池）
    长线=估值30+质地40+成长30（价值/蓝筹/成长三池）
    注：业务策略/产品进度暂无数据源，以营收增速为业务动能代理"""
    d = dates[-1] if dates else None
    if not d or d not in days:
        return {"short": [], "mid": [], "long": []}
    day = days[d]

    # ===== 短线：涨停池 + 潜龙 =====
    short = []
    ind_heat = {}
    for r in day["pools"]["zt"]:
        ind = r.get("所属行业") or "其他"
        ind_heat[ind] = ind_heat.get(ind, 0) + 1
    for r in day["pools"]["zt"]:
        an = r.get("_analysis") or {}
        at = r.get("_attr") or {}
        lb = int(r.get("连板数") or 0)
        tech = round((an.get("total") or 0) / 15 * 40, 1)  # 技术面：延续性评分
        emo = min(30, ind_heat.get(r.get("所属行业") or "其他", 0) * 4 + lb * 3)  # 情绪面：题材热度+梯队
        fund = 0
        fv = float(r.get("封板资金") or 0)
        if fv >= 1e8:
            fund = 20
        elif fv >= 3e7:
            fund = 12
        else:
            fund = 6
        t = str(r.get("首次封板时间") or "150000")
        if int(t[:2]) * 60 + int(t[2:4]) <= 600:
            fund += 10  # 早盘封板
        short.append({
            "code": r.get("代码"), "名称": r.get("名称"), "lb": lb,
            "score": round(tech + emo + fund, 1),
            "tech": tech, "emo": emo, "fund": fund,
            "why": (at.get("main") or "") + "驱动 · " + (r.get("_reason") or ""),
        })
    short.sort(key=lambda x: -x["score"])

    # ===== 中线：趋势池 =====
    mid = []
    fin = {}
    for c, roe, rg in conn.execute(
            "SELECT code, roe, rev_growth FROM fin_hist WHERE roe IS NOT NULL ORDER BY date"):
        fin[c] = (roe, rg)
    for r in (trend.get("pool") or []):
        tscore = r.get("score") or 0
        tech = round(min(40, tscore / 12 * 40), 1)
        f = fin.get(r["code"])
        roe_v = f[0] if f else None
        rg_v = f[1] if f else None
        funda = 0
        if roe_v is not None:
            funda += 3 if roe_v >= 15 else (2 if roe_v >= 10 else 1)
        if rg_v is not None and rg_v > 10:
            funda += 1
        funda = round(funda / 4 * 40, 1)
        vol = 20 if r.get("breakout") else (14 if r.get("pullback") else (10 if r.get("high60") else 6))
        mid.append({
            "code": r["code"], "名称": r["名称"],
            "score": round(tech + funda + vol, 1),
            "tech": tech, "funda": funda, "vol": vol,
            "why": (r.get("lv") or "") + " · " + ("突破" if r.get("breakout") else ("回踩" if r.get("pullback") else ("新高" if r.get("high60") else "均线多头"))),
        })
    mid.sort(key=lambda x: -x["score"])

    # ===== 长线：三池合并 =====
    long_ = []
    ai = set()
    bc = os.path.join(BASE, "growth_watchlist.json")
    if os.path.exists(bc):
        try:
            ai = set(json.load(open(bc, encoding="utf-8")).keys())
        except Exception:
            pass
    for pool_name, pool in [("价值", value.get("pool") or []), ("蓝筹", value.get("bluechip") or []), ("成长", value.get("growth") or [])]:
        for r in pool:
            val = 3 if r.get("pe_pct", 100) < 30 else (2 if r.get("pe_pct", 100) < 50 else 1)
            val = round(val / 3 * 30, 1)
            roe_v = r.get("roe")
            debt_v = r.get("debt")
            q = 0
            if roe_v is not None:
                q += 2.5 if roe_v >= 15 else (1.5 if roe_v >= 10 else 0.5)
            if debt_v is not None:
                q += 1.5 if debt_v < 50 else 0.5
            q = round(q / 4 * 40, 1)
            rg = r.get("rev_g")
            g = 0
            if rg is not None:
                g += 2 if rg > 30 else (1.2 if rg > 10 else 0.4)
            if r["code"] in ai:
                g += 1  # AI 硬件链标签（业务动能）
            g = round(min(3, g) / 3 * 30, 1)
            long_.append({
                "code": r["code"], "名称": r["名称"], "pool": pool_name,
                "score": round(val + q + g, 1),
                "val": val, "q": q, "g": g,
                "pe_pct": r.get("pe_pct"), "roe": roe_v, "rev_g": rg,
                "ai": r["code"] in ai,
                "why": r.get("val_tag", "") + " · ROE" + (str(roe_v) + "%" if roe_v is not None else "-") + (" · AI硬件链" if r["code"] in ai else ""),
            })
    long_.sort(key=lambda x: -x["score"])
    return {"short": short[:20], "mid": mid[:20], "long": long_[:20]}


def build(dates):
    conn = sqlite3.connect(DB)
    days = {}
    for d in dates:
        pools, breadth = load_day(conn, d)
        sent = sentiment(pools, breadth)
        analyze_stocks(pools, sent)
        themes, hl_conclusion = analyze_themes(pools, sent)
        ext = load_ext(conn, d)
        days[d] = {
            "breadth": breadth,
            "sent": sent,
            "pools": pools,
            "themes": themes,
            "hl": hl_conclusion,
            "ext": analyze_ext(ext, pools),
            "seats": analyze_seats(conn, d),
            "leaders": analyze_leaders(conn, d, pools, sent),
            "dragons": analyze_dragons(pools),
        }
    trend = analyze_trend(conn)
    value = analyze_value(conn)
    movement = analyze_movement(conn)
    lowpos = analyze_lowpos(conn)
    screener = analyze_screener(conn, days, dates, trend, value)
    news = load_news(conn)
    promotion = analyze_promotion(days, dates)
    news_map = build_name_map(conn, dates)
    conn.close()
    return {"dates": dates, "days": days, "trend": trend, "value": value, "movement": movement,
            "lowpos": lowpos, "screener": screener, "news": news,
            "promotion": promotion, "newsMap": news_map}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股短线看板 · 涨停接力复盘</title>
<style>
  :root{
    /* finesse Sage Ledger 变体 · Warm Stone 暖纸色阶 + 琥珀金 accent · 红涨绿跌语义独立 */
    --page:#f0ece5; --card:#ffffff; --ink:#1e1a14; --ink2:#4f473c; --ink3:#7f7462;
    --line:rgba(41,36,30,.09); --up:#C0392B; --upbg:#fdeeed; --down:#1E8A5F; --downbg:#e9f5ec;
    --blue:#2C5A6E; --bluebg:#e9f0f2; --amber:#B77A16; --amberbg:#faf3e4;
    --purple:#534ab7; --purplebg:#efedfc;
    --toolbar:#29241e; --toolbar-line:#3b352d;
    --accent:#B77A16; --accent-soft:rgba(183,122,22,.12);
    --shadow:0 1px 3px rgba(41,36,30,.06);
    --r:16px; --r-sm:11px;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:var(--page); color:var(--ink); font-family:"PingFang SC","Microsoft YaHei",-apple-system,sans-serif; line-height:1.55; font-size:13.5px;}
  .wrap{max-width:1320px; margin:0 auto; padding:22px 18px 60px;}
  .shell{background:var(--card); border:1px solid var(--border); border-radius:28px; padding:24px 26px 34px; box-shadow:0 40px 90px -50px rgba(41,36,30,.35); position:relative; overflow:hidden;}
  .shell::before{content:""; position:absolute; top:0; right:0; width:280px; height:200px; background:radial-gradient(280px 200px at 90% -10%, rgba(183,122,22,.13), transparent 60%); pointer-events:none;}
  .topbar{display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:14px; background:var(--toolbar); border:none; border-radius:var(--r-sm); padding:11px 18px; box-shadow:var(--shadow);}
  h1{font-size:16.5px; font-weight:600; color:#f5f1ea; letter-spacing:-.01em;}
  .sub{color:#a89c8e; font-size:12px;}
  .datebar{display:flex; gap:4px; flex-wrap:wrap;}
  .datebtn{border:1px solid var(--toolbar-line); background:transparent; border-radius:var(--r-sm); padding:4px 12px; font-size:12.5px; cursor:pointer; color:#c6bba9;}
  .datebtn:hover{color:#fff; border-color:#5a5142;}
  .datebtn.active{background:var(--accent); color:#fff; border-color:var(--accent); font-weight:600;}
  .card{background:var(--card); border:1px solid var(--border); border-radius:var(--r); padding:15px 17px; margin-bottom:12px; box-shadow:var(--shadow);}
  .tabs-wrap{margin-bottom:14px;}
  .tabs{display:flex; gap:0; border:1px solid var(--border); border-radius:var(--r-sm); overflow:hidden; background:var(--panel-2); width:fit-content;}
  .tabs label{padding:8px 20px; font-size:13px; cursor:pointer; color:var(--ink2); border-right:1px solid var(--border); background:transparent;}
  .tabs label:last-child{border-right:none;}
  .tabs label:hover{color:var(--accent); background:var(--panel-2);}
  #tab-short:checked ~ .tabs label[for="tab-short"],
  #tab-trend:checked ~ .tabs label[for="tab-trend"],
  #tab-value:checked ~ .tabs label[for="tab-value"]{background:var(--accent); color:#fff; border-color:var(--accent);}
  .sent-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr)); gap:8px;}
  .sent-item{border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:#fff; text-align:center;}
  .sent-item .label{font-size:11.5px; color:var(--ink2);}
  .sent-item .value{font-size:19px; font-weight:600; margin-top:1px;}
  .sent-item .subv{font-size:11.5px; color:var(--ink3); margin-top:2px;}
  .tag-big{font-size:15px; font-weight:600; padding:2px 12px; border-radius:8px; display:inline-block;}
  .tag-good{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .tag-danger{background:#4a0f0f; color:#ffd9d9; border:1px solid #7a1f1f;}
  .tag-warn{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .tag-flat{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .filters{display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end;}
  .f-item{display:flex; flex-direction:column; gap:4px;}
  .f-item label{font-size:11.5px; color:var(--ink2);}
  .f-item select,.f-item input{border:1px solid var(--line); border-radius:8px; padding:6px 10px; font-size:13px; background:#fff; color:var(--ink);}
  .f-item input{width:72px;}
  .ind-tags{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;}
  .ind-tag{border:1px solid var(--line); background:#fff; border-radius:16px; padding:3px 12px; font-size:12px; cursor:pointer; color:var(--ink2); user-select:none;}
  .ind-tag.on{background:var(--bluebg); color:var(--blue); border-color:#9cc4e8; font-weight:600;}
  .btn{border:1px solid var(--line); background:#fff; border-radius:8px; padding:6px 14px; font-size:13px; cursor:pointer; color:var(--ink2);}
  .btn:hover{border-color:var(--ink3);}
  .grp{margin-bottom:16px;}
  .grp-head{display:flex; align-items:center; gap:10px; margin-bottom:8px; padding:8px 12px; border-radius:10px; font-weight:600; font-size:14px;}
  .grp-head .cnt{font-size:12px; font-weight:400; color:var(--ink2);}
  .g-lb4{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0;}
  .g-lb3{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .g-lb2{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .g-lb1{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  table{width:100%; border-collapse:collapse; font-size:12px;}
  th{background:var(--panel-2); text-align:left; padding:6px 9px; border:1px solid var(--line); font-weight:600; white-space:nowrap; color:var(--ink2); font-size:11.5px;}
  td{padding:5px 9px; border:1px solid var(--line); white-space:nowrap; font-size:12px;}
  tr:nth-child(even) td{background:var(--panel-2);}
  tr:hover td{background:#f2f7fd;}
  .up{color:var(--up); font-weight:600;}
  .down{color:var(--down); font-weight:600;}
  .num{font-family:Consolas,"SF Mono",monospace; text-align:right; font-variant-numeric:tabular-nums;}
  .code{color:var(--ink2); font-family:Consolas,monospace;}
  .pill{display:inline-block; font-size:11px; border-radius:5px; padding:0 6px;}
  .pill-zt{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .pill-zb{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .pill-lv{border-radius:6px; padding:1px 8px; font-size:11.5px; font-weight:600;}
  .lv-strong{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .lv-mid{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .lv-weak{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .theme-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px;}
  .theme-card{border:1px solid var(--line); border-radius:8px; padding:11px 14px; background:#fff;}
  .theme-card .tname{font-weight:600; font-size:14px;}
  .theme-card .tmeta{font-size:12px; color:var(--ink2); margin-top:4px; line-height:1.8;}
  .stage-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600;}
  .st-good{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .st-warn{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .st-danger{background:#4a0f0f; color:#ffd9d9; border:1px solid #7a1f1f;}
  .st-flat{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .hl-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-left:6px;}
  .hl-good{background:var(--bluebg); color:var(--blue); border:1px solid #9cc4e8;}
  .hl-warn{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .hl-card{background:var(--bluebg); border:1px solid #c9ddef; border-radius:8px; padding:12px 16px; margin-top:12px; font-size:13px;}
  .hl-card b{color:var(--blue);}
  .empty{color:var(--ink3); text-align:center; padding:30px 0;}
  .foot{margin-top:20px; font-size:11.5px; color:var(--ink3); text-align:center;}
  .disclaimer{background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:10px 14px; font-size:12px; color:var(--ink2); margin-top:12px;}
  .lv-tip{cursor:help; border-bottom:1px dashed var(--ink3);}
  .sub-grid{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
  @media (max-width:900px){.sub-grid{grid-template-columns:1fr;}}
  .sub-box{border:1px solid var(--line); border-radius:8px; padding:12px 14px; background:#fff;}
  .sub-box h4{font-size:13.5px; margin-bottom:8px; color:var(--ink);}
  .lhb-row{display:flex; align-items:center; gap:8px; padding:5px 0; border-bottom:1px dashed var(--line); font-size:12.5px;}
  .lhb-row:last-child{border-bottom:none;}
  .lhb-row .nm{flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  .lhb-row .amt{font-family:Consolas,monospace; font-weight:600;}
  .money-in{color:var(--up);}
  .money-out{color:var(--down);}
  .focus-tag{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0; border-radius:5px; font-size:10.5px; padding:0 5px;}
  .attr-pill{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-right:2px;}
  .at-topic{background:var(--bluebg); color:var(--blue); border:1px solid #9cc4e8;}
  .at-money{background:var(--redbg); color:var(--red); border:1px solid #f3c4c2;}
  .at-tech{background:var(--greenbg); color:var(--green); border:1px solid #c2e3cc;}
  .at-msg{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .seat-tag{border-radius:5px; padding:1px 7px; font-size:10.5px; font-weight:600; margin-left:4px;}
  .seat-hot{background:var(--redbg); color:var(--red); border:1px solid #f3c4c2;}
  .seat-org{background:var(--bluebg); color:var(--blue); border:1px solid #9cc4e8;}
  .seat-quant{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .seat-ret{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .seat-oth{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .leader-badge{border-radius:6px; padding:2px 10px; font-size:12px; font-weight:600; margin-right:6px;}
  .lb-total{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0;}
  .lb-emo{background:var(--redbg); color:var(--red); border:1px solid #f3c4c2;}
  @media (max-width:760px){
    .wrap{padding:12px 8px 60px;}
    .hero{padding:16px 14px;}
    .card{padding:14px 12px; overflow-x:auto;}
    .topbar{flex-direction:column; align-items:flex-start; gap:8px;}
    h1{font-size:19px;}
    .sub{font-size:12.5px;}
    .datebar{flex-wrap:wrap;}
    .tabs{gap:0; margin-bottom:12px; width:100%;}
    .tabs label{padding:7px 0; font-size:13px; flex:1; text-align:center; min-width:0;}
    .filters{gap:8px;}
    .f-item{flex:1 1 44%;}
    .idx-grid{grid-template-columns:repeat(auto-fill,minmax(138px,1fr)); gap:8px;}
    .theme-grid{grid-template-columns:1fr;}
    .sub-grid,.two-col{grid-template-columns:1fr; gap:10px;}
    table{font-size:12px;}
    th,td{padding:5px 6px;}
    .lhb-row{flex-wrap:wrap;}
  }
  .desk-grid{display:grid; grid-template-columns:1fr; gap:14px;}
  .desk-grid .col{display:flex; flex-direction:column; gap:14px;}
  .desk-grid .card{margin-bottom:0;}
  @media (min-width:1024px){
    .desk-grid{grid-template-columns:200px 1.4fr 1fr; align-items:start;}
  }
  .nav-card{padding:14px 0 12px;}
  .brand{text-align:center;font-size:14px;font-weight:600;color:#fff;background:var(--blue);margin:-14px -1px 0 -1px;padding:10px;border-radius:0;}
  .brand-sub{text-align:center;font-size:11.5px;color:var(--ink3);margin:6px 0 10px;padding:0 10px;}
  .mod-btn{display:flex;align-items:center;gap:8px;padding:8px 12px;margin:2px 6px;font-size:12.5px;cursor:pointer;color:var(--ink2);border-radius:6px;border:1px solid transparent;background:transparent;}
  .mod-btn:hover{background:var(--panel-2);color:var(--ink);}
  .mod-btn.active{background:var(--bluebg);color:var(--blue);border-color:#9cc4e8;font-weight:600;}
  .mod-btn .ic{font-size:14px;width:16px;text-align:center;color:var(--ink3);}
  .mod-btn.active .ic{color:var(--blue);}
  .mod-sep{height:1px;background:var(--line);margin:8px 12px;}
  .toolbar{display:flex;align-items:center;justify-content:space-between;padding:6px 0 10px;border-bottom:1px solid var(--line);margin-bottom:12px;flex-wrap:wrap;gap:6px;}
  .tb-title{font-size:14px;font-weight:600;}
  .tb-title .cnt{font-weight:400;color:var(--ink2);font-size:12px;margin-left:6px;}
  .tb-tip{font-size:11.5px;color:var(--ink3);}
  .lb-tag{font-size:11.5px;font-weight:600;padding:1px 8px;border-radius:5px;margin-right:6px;}
  .t-lb7{background:#4a0f0f;color:#fff;}
  .t-lb5{background:#d93025;color:#fff;}
  .t-lb4{background:#fdecec;color:#d93025;border:1px solid #f3c4c2;}
  .t-lb3{background:#fdf3e0;color:#b45309;border:1px solid #f0d9ac;}
  .t-lb2{background:#e8f1fa;color:#185fa5;border:1px solid #c9ddef;}
  .t-lb1{background:var(--panel-2);color:#5a6472;border:1px solid #dde2e8;}
  .g-lb7{background:#4a0f0f;color:#fff;}
  .g-lb5{background:#fdecec;color:#4a0f0f;}
  .g-lb4{background:#fdecec;color:#a32d2d;}
  .g-lb3{background:#fdf3e0;color:#854f0b;}
  .g-lb2{background:#e8f1fa;color:#1d5fa8;}
  .g-lb1{background:var(--panel-2);color:#5a6472;}
  .metric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px;}
  .metric-card{border:1px solid var(--line);border-radius:6px;padding:10px;background:#fff;text-align:center;}
  .metric-card .lab{font-size:11.5px;color:var(--ink2);}
  .metric-card .val{font-size:18px;font-weight:600;margin-top:2px;font-family:Consolas,monospace;font-variant-numeric:tabular-nums;letter-spacing:-.01em;}
  .core-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:12px;}
  .core-cell{border:1px solid var(--line);border-radius:6px;padding:8px;background:#fff;text-align:center;}
  .core-cell .lab{font-size:11px;color:var(--ink2);}
  .core-cell .val{font-size:17px;font-weight:600;margin-top:1px;font-family:Consolas,monospace;font-variant-numeric:tabular-nums;}
  .temp-bar{margin:8px 0 4px;}
  .temp-track{position:relative;height:8px;background:linear-gradient(90deg,#185fa5 0%,#188038 50%,#d93025 100%);border-radius:4px;margin:6px 0;}
  .temp-fill{height:100%;background:rgba(255,255,255,0.4);border-radius:4px;}
  .temp-marker{position:absolute;top:-4px;width:4px;height:16px;background:#1f2430;border-radius:2px;transform:translateX(-50%);}
  .temp-labels{display:flex;justify-content:space-between;font-size:10px;color:var(--ink3);padding:2px 0;}
  .risk-line{display:flex;justify-content:space-between;align-items:center;padding:6px 4px;margin-top:6px;background:var(--panel-2);border-radius:6px;font-size:11px;color:var(--ink2);}
  .tone-tag{display:inline-block;font-size:15px;font-weight:600;padding:4px 14px;border-radius:8px;margin-bottom:8px;}
  .prev-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px dashed var(--line);font-size:12.5px;}
  .prev-row:last-child{border-bottom:none;}
  .theme-row,.dragon-row{padding:6px 0;border-bottom:1px dashed var(--line);font-size:12.5px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
  .theme-row:last-child,.dragon-row:last-child{border-bottom:none;}
  .view .card{padding:14px 16px;}
  .scr-tabs{display:flex;gap:0;border:1px solid var(--line);border-radius:6px;overflow:hidden;}
  .scr-btn{border:none;background:#fff;padding:5px 16px;font-size:12.5px;cursor:pointer;color:var(--ink2);border-right:1px solid var(--line);}
  .scr-btn:last-child{border-right:none;}
  .scr-btn:hover{background:var(--panel-2);}
  .scr-btn.active{background:var(--accent);color:#fff;font-weight:600;}
  .scr-note{font-size:11.5px;color:var(--ink3);background:var(--panel-2);border:1px solid var(--line);border-radius:6px;padding:6px 10px;margin-bottom:10px;line-height:1.6;}
  .scr-score{color:var(--blue);font-size:13px;}
  .d-up{color:var(--up);font-weight:600;}
  .d-dn{color:var(--down);font-weight:600;}
  .d-flat{color:var(--ink2);}
  .d-none{color:var(--ink3);}
  .d-base{font-size:10px;color:var(--ink3);margin-left:2px;}
  .co-link{color:var(--accent);font-weight:600;text-decoration:none;border-bottom:1px dashed var(--accent);}
  .co-link:hover{background:var(--accent-soft);}
  .news-cats{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;}
  .cat-btn{border:1px solid var(--border);background:var(--panel-2);border-radius:999px;padding:4px 14px;font-size:12.5px;cursor:pointer;color:var(--ink2);}
  .cat-btn:hover{border-color:var(--accent);color:var(--accent);}
  .cat-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;}
  .cat-btn .n{font-size:11px;opacity:.75;margin-left:2px;}
  .tl{position:relative;padding-left:18px;}
  .tl::before{content:"";position:absolute;left:4px;top:6px;bottom:6px;width:1px;background:var(--border);}
  .tl-item{position:relative;padding:0 0 14px 0;margin-bottom:12px;border-bottom:1px dashed var(--border);}
  .tl-item:last-child{border-bottom:none;margin-bottom:0;}
  .tl-item::before{content:"";position:absolute;left:-17px;top:5px;width:7px;height:7px;border-radius:50%;background:var(--accent);}
  .tl-time{font-size:11px;color:var(--ink3);font-family:Consolas,monospace;margin-bottom:3px;display:flex;align-items:center;gap:8px;}
  .tl-src{font-size:10px;background:var(--panel-2);border-radius:4px;padding:0 6px;color:var(--ink3);}
  .tl-title{font-size:13.5px;font-weight:600;color:var(--ink);text-decoration:none;line-height:1.5;display:block;}
  .tl-title:hover{color:var(--accent);}
  .tl-sum{font-size:12px;color:var(--ink2);line-height:1.65;margin-top:4px;}
  .kw{color:var(--up);font-weight:700;font-style:normal;background:var(--upbg);border-radius:3px;padding:0 2px;}
  .ana{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:7px;padding:6px 10px;border-radius:8px;font-size:11.5px;background:var(--panel-2);}
  .ana.pos .ana-tag{background:var(--upbg);color:var(--up);border:1px solid #f3c4c2;}
  .ana.neg .ana-tag{background:var(--downbg);color:var(--down);border:1px solid #c2e3cc;}
  .ana.neu .ana-tag{background:var(--panel-2);color:var(--ink3);border:1px solid var(--border);}
  .ana-tag{font-weight:600;padding:1px 8px;border-radius:5px;font-size:11px;}
  .ana-why{color:var(--ink2);flex:1;min-width:180px;}
  .ana-cat{color:var(--ink3);font-size:10.5px;border:1px solid var(--border);border-radius:4px;padding:0 6px;}
  @media (max-width:1023px){
    .col-nav{order:1;} .col-main{order:2;} .col-side{order:3;}
    .metric-grid{grid-template-columns:repeat(3,1fr);}
    .core-grid{grid-template-columns:repeat(3,1fr);}
  }
  .cycle-wrap{display:flex; align-items:stretch; gap:5px; padding-top:6px;}
  .cycle-day{flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:3px; min-width:0;}
  .c-bars{display:flex; align-items:flex-end; gap:2px; height:74px; width:100%; justify-content:center;}
  .c-bar{border-radius:3px 3px 0 0; min-height:3px;}
  .c-bar.zt{background:var(--red); width:42%;}
  .c-bar.dt{background:var(--green); width:42%;}
  .c-maxlb{font-size:12px; color:var(--ink2); font-weight:600;}
  .c-tag{font-size:10px; padding:0 5px; border-radius:4px; line-height:1.5;}
  .c-tag.tag-danger{background:var(--redbg); color:var(--red);}
  .c-tag.tag-good{background:var(--greenbg); color:var(--green);}
  .c-tag.tag-warn{background:var(--amberbg); color:var(--amber);}
  .c-tag.tag-flat{background:var(--panel-2); color:var(--ink2);}
  .c-label{font-size:10px; color:var(--ink3);}
  .cycle-day.cycle-cur .c-maxlb{color:var(--red);}
  .cycle-day.cycle-cur .c-label{color:var(--red); font-weight:600;}
  .cycle-hint{font-size:11.5px; color:var(--ink3); margin-top:6px;}
  .prev-stats{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px;}
  .prev-stat{border:1px solid var(--line); border-radius:8px; padding:8px 16px; background:#fff; text-align:center; min-width:90px;}
  .prev-stat .v{font-size:18px; font-weight:600;}
  .prev-stat .l{font-size:11px; color:var(--ink2);}
  .two-col{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
  @media (max-width:900px){.two-col{grid-template-columns:1fr;}}
  .mini-list{border:1px solid var(--line); border-radius:8px; padding:8px 10px; background:#fff; font-size:12px;}
  .mini-list .row{padding:3px 0; border-bottom:1px dashed var(--line); display:flex; gap:6px; align-items:center;}
  .mini-list .row:last-child{border-bottom:none;}
  .mini-list .c{color:var(--ink3); font-family:Consolas,monospace; font-size:11px;}
  .tabs-wrap input{display:none;}
  .tabs{display:flex; gap:0; margin:0 0 12px; border:1px solid var(--line); border-radius:8px; overflow:hidden; background:#fff; width:fit-content;}
  .tabs label{display:inline-block; padding:8px 20px; border-right:1px solid var(--line); cursor:pointer; font-size:13px; background:#fff; color:var(--ink2); user-select:none; font-weight:500;}
  .tabs label:last-child{border-right:none;}
  #tab-short:checked ~ .tabs label[for="tab-short"],
  #tab-trend:checked ~ .tabs label[for="tab-trend"],
  #tab-value:checked ~ .tabs label[for="tab-value"]{background:var(--blue); color:#fff; border-color:var(--blue);}
  .panel{display:none;}
  #tab-short:checked ~ .panel-short,
  #tab-trend:checked ~ .panel-trend,
  #tab-value:checked ~ .panel-value{display:block;}
  .idx-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:10px;}
  .idx-card{border:1px solid var(--line); border-radius:8px; padding:10px 14px; background:#fff;}
  .idx-card .iname{font-weight:600; font-size:13.5px;}
  .idx-card .ival{font-size:16px; font-weight:600; margin:2px 0;}
  .idx-card .imeta{font-size:11.5px; color:var(--ink2); line-height:1.7;}
  .st-bull{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2; border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .st-bear{background:var(--downbg); color:var(--down); border:1px solid #c2e3cc; border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .st-mix{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line); border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .sig-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-right:4px;}
  .sig-bk{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0;}
  .sig-pb{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .sig-hi{background:var(--bluebg); color:var(--blue); border:1px solid #9cc4e8;}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
<div class="wrap">
<div class="shell">
  <div class="topbar">
    <div>
      <h1>A股行情看板 · 短线 + 中长线趋势</h1>
      <div class="sub" id="subline"></div>
    </div>
    <div class="datebar" id="datebar"></div>
  </div>

  <div class="tabs-wrap">
    <input type="radio" name="mod" id="tab-short" checked>
    <input type="radio" name="mod" id="tab-trend">
    <input type="radio" name="mod" id="tab-value">
    <div class="tabs">
      <label for="tab-short">短线复盘</label>
      <label for="tab-trend">中长线趋势</label>
      <label for="tab-value">长线价值</label>
    </div>

  <div class="panel panel-short">
  <div class="desk-grid">
    <div class="col col-nav">
      <div class="card nav-card">
        <div class="brand">A股复盘台</div>
        <div class="brand-sub" id="brand-sub">短线 · 涨停梯队</div>
        <div id="nav-modules"></div>
      </div>

      <div class="card">
        <div style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--ink2);">梯队筛选</div>
        <div class="filters">
          <div class="f-item">
            <label>连板数</label>
            <select id="f-lb">
              <option value="0">全部</option>
              <option value="1">仅首板</option>
              <option value="2">2板</option>
              <option value="3">3板</option>
              <option value="4">4板及以上</option>
            </select>
          </div>
          <div class="f-item">
            <label>换手率 %</label>
            <div style="display:flex; gap:6px; align-items:center;">
              <input type="number" id="f-turn-min" placeholder="0" min="0" max="100">
              <span style="color:var(--ink3); font-size:12px;">~</span>
              <input type="number" id="f-turn-max" placeholder="100" min="0" max="100">
            </div>
          </div>
          <div class="f-item">
            <label>封板时间</label>
            <select id="f-seal">
              <option value="all">全部</option>
              <option value="early">早盘 ≤10:00</option>
              <option value="mid">盘中</option>
              <option value="late">尾盘 ≥14:30</option>
            </select>
          </div>
          <div class="f-item">
            <label>炸板</label>
            <select id="f-zb">
              <option value="all">全部</option>
              <option value="0">0 次</option>
              <option value="1">≥1 次</option>
            </select>
          </div>
          <div class="f-item">
            <label>操作</label>
            <button class="btn" id="f-reset" type="button">重置</button>
          </div>
        </div>
        <div class="ind-tags" id="ind-tags"></div>
      </div>
    </div>

    <div class="col col-main">
      <div class="view" id="view-stage">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">涨停梯队 <span class="cnt" id="stage-cnt"></span></div>
            <div class="tb-tip" id="stage-tip"></div>
          </div>
          <div id="stage-body"></div>
        </div>
        <div class="card">
          <div id="promo-body"></div>
        </div>
      </div>
      <div class="view" id="view-alert" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">溢价 · 异动预警</div>
            <div class="tb-tip" id="alert-tip"></div>
          </div>
          <div id="alert-body"></div>
        </div>
      </div>
      <div class="view" id="view-cycle" style="display:none">
        <div class="card">
          <div class="toolbar"><div class="tb-title">情绪 · 周期</div></div>
          <div id="cycle-body"></div>
        </div>
      </div>
      <div class="view" id="view-theme" style="display:none">
        <div class="card">
          <div class="toolbar"><div class="tb-title">主线 · 龙头 · 潜龙</div></div>
          <div id="theme-body"></div>
        </div>
      </div>
      <div class="view" id="view-news" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">公告资讯 <span class="cnt" id="news-cnt"></span></div>
            <div class="tb-tip">按发布时间倒序 · 关键词红字高亮</div>
          </div>
          <div id="news-body"></div>
        </div>
      </div>
      <div class="view" id="view-screener" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">多因子选股器 <span class="cnt" id="scr-cnt"></span></div>
            <div class="scr-tabs">
              <button class="scr-btn active" data-m="short" onclick="setScrMode('short')">短线</button>
              <button class="scr-btn" data-m="mid" onclick="setScrMode('mid')">中线</button>
              <button class="scr-btn" data-m="long" onclick="setScrMode('long')">长线</button>
            </div>
          </div>
          <div class="scr-note" id="scr-note"></div>
          <div id="scr-body"></div>
        </div>
      </div>
    </div>

      <div class="col col-side">
        <div class="card">
          <div id="side-tone"></div>
        </div>
      <div class="card">
        <div id="side-coredata"></div>
      </div>
      <div class="card">
        <div id="side-prev"></div>
      </div>
    </div>
  </div>
  </div>

  <div class="panel panel-trend">
    <div class="card">
      <div id="trend-idx"></div>
    </div>
    <div class="card">
      <div class="filters">
        <div class="f-item">
          <label>强度档位</label>
          <select id="t-lv">
            <option value="all">全部</option>
            <option value="强">仅强</option>
            <option value="中">中及以上</option>
          </select>
        </div>
        <div class="f-item">
          <label>信号</label>
          <select id="t-sig">
            <option value="all">全部</option>
            <option value="bk">仅突破</option>
            <option value="pb">仅回踩</option>
            <option value="hi">仅新高</option>
          </select>
        </div>
        <div class="f-item">
          <label>筛选</label>
          <button class="btn" id="t-reset" type="button">重置</button>
        </div>
      </div>
      <div id="trend-pool" style="margin-top:12px;"></div>
    </div>
  </div>

  <div class="panel panel-value">
    <div class="card">
      <div id="value-card"></div>
    </div>
  </div>
  </div>

  <div class="disclaimer"><b>免责声明：</b>本看板数据来自公开行情接口（东方财富/乐咕乐股），仅供个人复盘研究参考，不构成投资建议。市场有风险，投资需谨慎。涨停原因、题材归类等字段将在后续版本完善。</div>
  <div class="foot">A股短线看板 · 由 _gen_board.py 生成 · 数据仅供复盘参考</div>
</div>
</div>

<script>
window.BOARD_DATA = __DATA__;
</script>
<script>
(function () {
  "use strict";
  var data = window.BOARD_DATA;
  var cur = data.dates[data.dates.length - 1];
  var filters = { lb: 0, turnMin: 0, turnMax: 100, seal: "all", zb: "all", inds: {} };

  function fmtDate(d) {
    return d.slice(0, 4) + "-" + d.slice(4, 6) + "-" + d.slice(6, 8);
  }
  function fmtMoney(v) {
    if (v === null || v === undefined) return "-";
    v = Number(v);
    if (v >= 100000000) return (v / 100000000).toFixed(2) + "亿";
    if (v >= 10000) return (v / 10000).toFixed(0) + "万";
    return String(v);
  }
  function fmtSeal(t) {
    if (!t) return "-";
    t = String(t);
    return t.slice(0, 2) + ":" + t.slice(2, 4);
  }
  function esc(s) {
    return String(s === null || s === undefined ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderDatebar() {
    var bar = document.getElementById("datebar");
    bar.innerHTML = "";
    data.dates.forEach(function (d) {
      var b = document.createElement("button");
      b.className = "datebtn" + (d === cur ? " active" : "");
      b.textContent = fmtDate(d).slice(5);
      b.onclick = function () { cur = d; renderAll(); };
      bar.appendChild(b);
    });
  }

  function renderSentiment() {
    var day = data.days[cur];
    var s = day.sent;
    var b = day.breadth;
    var sub = "数据截至 " + fmtDate(cur) + " 收盘 · 涨停池/跌停池/炸板池来自东方财富 · 广度来自乐咕乐股";
    document.getElementById("subline").textContent = sub;

    var items = [
      ["涨停", s.zt, b && b.real_zt !== null && b.real_zt !== undefined ? "真实涨停 " + b.real_zt : "连板高度 " + (s.max_lb || 0) + "板"],
      ["跌停", s.dt, b && b.real_dt ? "真实跌停 " + b.real_dt : ""],
      ["炸板", s.zb, "炸板率 " + s.zbrate + "%"],
      ["连板高度", s.max_lb + "板", s.top.length ? (s.top[0]['名称'] + " " + s.top[0].ztstat) : "无连板"],
      ["上涨家数", b ? b.up : "-", b ? "占比 " + (b.total ? Math.round(b.up / b.total * 100) : 0) + "%" : ""],
      ["下跌家数", b ? b.down : "-", b ? "占比 " + (b.total ? Math.round(b.down / b.total * 100) : 0) + "%" : ""],
      ["活跃度", b && b.activity ? b.activity : "-", "市场参与热度"],
    ];
    var html = '<div class="sent-grid">';
    items.forEach(function (it) {
      html += '<div class="sent-item"><div class="label">' + it[0] + '</div><div class="value">' + it[1] + '</div>' +
              (it[2] ? '<div class="subv">' + it[2] + '</div>' : '') + '</div>';
    });
    html += '<div class="sent-item"><div class="label">情绪标签</div><div class="value" style="padding-top:4px;"><span class="tag-big tag-' + s.tag_cls + '">' + s.tag + '</span></div><div class="subv">规则引擎 v0</div></div>';
    html += '</div>';
    document.getElementById("sentiment").innerHTML = html;
  }

  function buildIndTags() {
    var day = data.days[cur];
    var set = {};
    day.pools.zt.forEach(function (r) {
      var ind = r["所属行业"];
      if (ind) set[ind] = (set[ind] || 0) + 1;
    });
    var keys = Object.keys(set).sort(function (a, b) { return set[b] - set[a]; });
    var box = document.getElementById("ind-tags");
    box.innerHTML = "";
    keys.forEach(function (k) {
      var t = document.createElement("span");
      t.className = "ind-tag" + (filters.inds[k] ? " on" : "");
      t.textContent = k + " (" + set[k] + ")";
      t.onclick = function () {
        filters.inds[k] = !filters.inds[k];
        renderPool();
        buildIndTags();
      };
      box.appendChild(t);
    });
  }

  function sealToMin(t) {
    if (!t) return 9999;
    t = String(t);
    return parseInt(t.slice(0, 2), 10) * 60 + parseInt(t.slice(2, 4), 10);
  }
  function sealLabel(v) {
    if (v <= 600) return "早盘";
    if (v < 870) return "盘中";
    return "尾盘";
  }

  function filterList(list) {
    return list.filter(function (r) {
      var lb = parseInt(r["连板数"] || 0, 10);
      if (filters.lb === 4 && lb < 4) return false;
      if (filters.lb > 0 && filters.lb < 4 && lb !== filters.lb) return false;
      var turn = Number(r["换手率"] || 0);
      if (turn < filters.turnMin || turn > filters.turnMax) return false;
      if (filters.seal !== "all") {
        var m = sealToMin(r["首次封板时间"]);
        if (filters.seal === "early" && m > 600) return false;
        if (filters.seal === "mid" && (m <= 600 || m >= 870)) return false;
        if (filters.seal === "late" && m < 870) return false;
      }
      if (filters.zb === "0" && parseInt(r["炸板次数"] || 0, 10) !== 0) return false;
      if (filters.zb === "1" && parseInt(r["炸板次数"] || 0, 10) === 0) return false;
      if (Object.keys(filters.inds).length) {
        if (!filters.inds[r["所属行业"]]) return false;
      }
      return true;
    });
  }

  function renderThemes() {
    var day = data.days[cur];
    var box = document.getElementById("themes-card");
    if (!day.themes || !day.themes.length) { box.innerHTML = ""; return; }
    var html = '<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:12px;">' +
      '<div style="font-weight:600; font-size:15px;">题材分析 · 板块整体</div>' +
      '<div style="font-size:12px; color:var(--ink2);">共 ' + day.themes.length + ' 个题材（按行业聚合）</div></div>';
    html += '<div class="theme-grid">';
    day.themes.forEach(function (t) {
      html += '<div class="theme-card">' +
        '<div><span class="tname">' + esc(t['名称']) + '</span>' +
        '<span class="stage-tag st-' + t.stage_cls + '">' + t.stage + '</span>' +
        (t.hl ? '<span class="hl-tag hl-' + t.hl_cls + '">' + t.hl + '</span>' : '') + '</div>' +
        '<div class="tmeta">涨停 <b>' + t.count + '</b> 家 · 高度 ' + t.max_lb + '板 (' + t.lb_names + ')<br>' +
        '封板资金 ' + t.total_seal + '亿 · 龙头 <b>' + esc(t.leader['名称']) + '</b> (' + t.leader.lb + '板)</div>' +
        '</div>';
    });
    html += '</div>';
    if (day.hl && day.hl.text) {
      html += '<div class="hl-card"><b>高低切观察（板块间）</b>：' + esc(day.hl.text) + '<br><b>明日核心变量</b>：' + esc(day.hl.watch) + '</div>';
    }
    box.innerHTML = html;
  }

  function renderPool() {
    var day = data.days[cur];
    var list = filterList(day.pools.zt);
    var groups = {};
    list.forEach(function (r) {
      var lb = Math.min(parseInt(r["连板数"] || 0, 10), 4);
      (groups[lb] = groups[lb] || []).push(r);
    });
    var order = [4, 3, 2, 1];
    var names = { 4: "空间板 · 4板及以上", 3: "三连板", 2: "二连板", 1: "首板" };
    var colors = { 4: "g-lb4", 3: "g-lb3", 2: "g-lb2", 1: "g-lb1" };
    var box = document.getElementById("pool");
    if (!list.length) { box.innerHTML = '<div class="empty">无符合条件的涨停股</div>'; return; }
    var html = '<div style="color:var(--ink2);font-size:12.5px;margin-bottom:10px;">共 ' + list.length + ' 只（' +
               (Object.keys(filters.inds).length ? "已按盘口筛选" : "全部") + '）· 悬停延续性标签查看次日策略</div>';
    order.forEach(function (lb) {
      var arr = groups[lb];
      if (!arr) return;
      html += '<div class="grp"><div class="grp-head ' + colors[lb] + '">' + names[lb] + ' <span class="cnt">' + arr.length + ' 只</span></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>涨幅</th><th>涨停价</th><th>几天几板</th><th>涨停原因</th><th>换手率</th><th>封板资金</th><th>首封</th><th>炸板</th><th>延续性</th></tr>';
      arr.forEach(function (r) {
        var ztstat = r["涨停统计"] ? esc(r["涨停统计"]) : (parseInt(r["连板数"] || 0, 10) + "天" + (r["连板数"] || 0) + "板");
        var an = r["_analysis"] || {};
        var tip = "延续性:" + an.total + "分\n" + an.strat + "\n风控:" + an.risk;
        var at = r["_attr"] || {};
        var attrPill = '';
        if (at.main) {
          var ac = at.main === "题材" ? "at-topic" : (at.main === "资金" ? "at-money" : (at.main === "技术" ? "at-tech" : "at-msg"));
          attrPill = '<span class="attr-pill ' + ac + '" title="题材' + at.topic + '% / 资金' + at.money + '% / 技术' + at.tech + '% / 消息' + at.msg + '%">' + at.main + '</span>';
        }
        html += '<tr>' +
          '<td class="code">' + esc(r["代码"]) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="up num">' + Number(r["涨跌幅"]).toFixed(2) + '%</td>' +
          '<td class="num">' + Number(r["最新价"]).toFixed(2) + '</td>' +
          '<td>' + ztstat + '</td>' +
          '<td>' + attrPill + ' ' + esc(r["_reason"] || r["所属行业"] || "-") + '</td>' +
          '<td class="num">' + (r["换手率"] !== null && r["换手率"] !== undefined ? Number(r["换手率"]).toFixed(2) + '%' : '-') + '</td>' +
          '<td class="num">' + fmtMoney(r["封板资金"]) + '</td>' +
          '<td class="num">' + fmtSeal(r["首次封板时间"]) + ' <span class="pill ' + (sealLabel(sealToMin(r["首次封板时间"])) === "早盘" ? "pill-zt" : "pill-zb") + '">' + sealLabel(sealToMin(r["首次封板时间"])) + '</span></td>' +
          '<td class="num">' + parseInt(r["炸板次数"] || 0, 10) + '</td>' +
          '<td><span class="pill-lv ' + (an.level_cls || "lv-weak") + ' lv-tip" title="' + esc(tip) + '">' + (an.level || "-") + '</span></td>' +
          '</tr>';
      });
      html += '</table></div>';
    });
    box.innerHTML = html;
  }

  function renderExt() {
    var day = data.days[cur];
    var ext = day.ext;
    var box = document.getElementById("ext-card");
    if (!ext) { box.innerHTML = ""; return; }
    var hasLhb = ext.lhb_top_buy.length > 0;
    var hasFund = ext.fund_in.length > 0;
    var prev = ext.prev;
    if (!hasLhb && !hasFund && !prev) { box.innerHTML = ""; return; }

    var html = '<div style="font-weight:600; font-size:15px; margin-bottom:12px;">资金透视 · 复盘闭环</div>';

    if (prev) {
      var jc = prev.jn / prev.total * 100;
      html += '<div class="prev-stats">' +
        '<div class="prev-stat"><div class="v ' + (jc >= 30 ? "money-in" : "") + '">' + prev.jn_rate + '%</div><div class="l">昨日涨停晋级率</div></div>' +
        '<div class="prev-stat"><div class="v money-in">' + prev.jn + '</div><div class="l">晋级（连板）</div></div>' +
        '<div class="prev-stat"><div class="v">' + prev.db + '</div><div class="l">断板</div></div>' +
        '<div class="prev-stat"><div class="v ' + (prev.avg_pct >= 0 ? "money-in" : "money-out") + '">' + prev.avg_pct + '%</div><div class="l">昨日涨停今均涨</div></div>' +
        '</div>';
      html += '<div class="two-col">';
      html += '<div class="mini-list"><div style="font-weight:600;font-size:12.5px;margin-bottom:4px;">晋级名单（今仍涨停）</div>';
      prev.jn_list.forEach(function (r) {
        html += '<div class="row"><span class="c">' + esc(r["代码"]) + '</span><b>' + esc(r["名称"]) + '</b><span class="money-in">' + Number(r["涨跌幅"]).toFixed(2) + '%</span><span style="color:var(--ink3);">' + esc(r["涨停统计"] || "") + '</span><span style="margin-left:auto;color:var(--ink3);">' + esc(r["所属行业"] || "") + '</span></div>';
      });
      html += '</div>';
      html += '<div class="mini-list"><div style="font-weight:600;font-size:12.5px;margin-bottom:4px;">断板名单（今未封住）</div>';
      prev.db_list.forEach(function (r) {
        html += '<div class="row"><span class="c">' + esc(r["代码"]) + '</span><b>' + esc(r["名称"]) + '</b><span class="' + (Number(r["涨跌幅"]) >= 0 ? "money-in" : "money-out") + '">' + Number(r["涨跌幅"]).toFixed(2) + '%</span><span style="margin-left:auto;color:var(--ink3);">' + esc(r["所属行业"] || "") + '</span></div>';
      });
      html += '</div></div>';
    }

    if (hasLhb || hasFund) {
      var seats = day.seats || { stocks: {}, hot: [] };
      var seatTagCls = { "知名游资": "seat-hot", "机构": "seat-org", "量化": "seat-quant", "散户通道": "seat-ret", "其他": "seat-oth" };
      html += '<div class="sub-grid" style="margin-top:12px;">';
      if (hasLhb) {
        html += '<div class="sub-box"><h4>龙虎榜 · 净买额 TOP（' + (ext.lhb_zt.length ? "★涨停+上榜焦点" : "当日上榜") + '）</h4>';
        var list = ext.lhb_zt.length ? ext.lhb_zt : ext.lhb_top_buy;
        list.slice(0, 8).forEach(function (r) {
          var net = Number(r["龙虎榜净买额"] || 0);
          var st = seats.stocks[r["代码"]] || [];
          var stHtml = st.slice(0, 2).map(function (s) {
            return '<span class="seat-tag ' + (seatTagCls[s.tag] || "seat-oth") + '">' + s.tag + '</span>';
          }).join('');
          html += '<div class="lhb-row"><span class="nm"><b>' + nameLink(r) + '</b> <span class="c">' + esc(r["代码"]) + '</span>' +
            (ext.lhb_zt.indexOf(r) >= 0 ? ' <span class="focus-tag">涨停</span>' : '') + stHtml + '</span>' +
            '<span class="amt ' + (net >= 0 ? "money-in" : "money-out") + '">' + (net >= 0 ? "+" : "") + fmtMoney(net) + '</span></div>';
        });
        html += '</div>';
      }
      if (hasFund) {
        html += '<div class="sub-box"><h4>板块资金流 · 行业净流入 TOP</h4>';
        ext.fund_in.slice(0, 6).forEach(function (r) {
          html += '<div class="lhb-row"><span class="nm"><b>' + esc(r["行业"]) + '</b> <span style="color:var(--ink3);">' + Number(r["行业-涨跌幅"]).toFixed(2) + '%</span></span>' +
            '<span class="amt money-in">+' + Number(r["净额"]).toFixed(2) + '亿</span></div>';
        });
        html += '<div style="font-weight:600;font-size:12.5px;margin:10px 0 2px;">净流出 TOP</div>';
        ext.fund_out.slice(0, 3).forEach(function (r) {
          html += '<div class="lhb-row"><span class="nm">' + esc(r["行业"]) + '</span>' +
            '<span class="amt money-out">' + Number(r["净额"]).toFixed(2) + '亿</span></div>';
        });
        html += '</div>';
      }
      if (seats.hot && seats.hot.length) {
        html += '<div class="sub-box"><h4>游资动向 · 知名游资今日动作（买卖双向）</h4>';
        seats.hot.slice(0, 8).forEach(function (r) {
          var cls = r.hist_n >= 3 ? "seat-hot" : "seat-oth";
          var isBuy = r.net > 0;
          html += '<div class="lhb-row"><span class="nm"><b>' + esc(r.name) + '</b> <span class="c">' + esc(r.code) + '</span> ' +
            '<span class="seat-tag ' + cls + '">' + esc(shortSeat(r.seat)) + (r.hist_n ? ' · ' + r.hist_n + '次' : '') +
            (r.hist_win !== null && r.hist_win !== undefined ? ' · 胜率' + r.hist_win + '%' : '') + '</span>' +
            (isBuy ? ' <span class="focus-tag" style="background:var(--redbg);color:var(--red);border-color:#f3c4c2;">买</span>' : ' <span class="focus-tag" style="background:var(--greenbg);color:var(--green);border-color:#c2e3cc;">卖</span>') +
            '</span>' +
            '<span class="amt ' + (isBuy ? "money-in" : "money-out") + '">' + (isBuy ? "+" : "") + fmtMoney(r.net) + '</span></div>';
        });
        html += '</div>';
      }
      html += '</div>';
    }
    box.innerHTML = html;
  }

  function shortSeat(s) {
    s = String(s || "");
    s = s.replace(/证券股份有限公司|有限责任公司|证券营业部/g, "");
    return s.length > 14 ? s.slice(0, 13) + "…" : s;
  }

  var tFilters = { lv: "all", sig: "all" };

  function renderTrend() {
    var tr = data.trend;
    var boxIdx = document.getElementById("trend-idx");
    if (!tr || !tr.idx) { boxIdx.innerHTML = '<div class="empty">趋势数据采集中，今晚 21:30 自动更新后可见</div>'; return; }
    var html = '<div style="font-weight:600; font-size:15px; margin-bottom:12px;">指数趋势状态 <span style="font-size:12px;color:var(--ink2);font-weight:400;">MA20/MA60/MA120 · 基准 20 日涨幅 ' + tr.bench20 + '%</span></div>';
    html += '<div class="idx-grid">';
    Object.keys(tr.idx).forEach(function (nm) {
      var it = tr.idx[nm];
      var cls = it.status === "多头" ? "st-bull" : (it.status === "空头" ? "st-bear" : "st-mix");
      html += '<div class="idx-card"><div class="iname">' + esc(nm) + '</div>' +
        '<div class="ival">' + it.close + '</div>' +
        '<div class="imeta"><span class="' + cls + '">' + it.status + '</span> 20日 ' +
        (it.pct20 >= 0 ? '<span class="money-in">+' : '<span class="money-out">') + it.pct20 + '%</span><br>' +
        'MA20 ' + it.ma20 + ' / MA60 ' + it.ma60 + (it.ma120 ? ' / MA120 ' + it.ma120 : '') + '</div></div>';
    });
    html += '</div>';
    boxIdx.innerHTML = html;

    var list = tr.pool.filter(function (r) {
      if (tFilters.lv === "强" && r.lv !== "强") return false;
      if (tFilters.lv === "中" && r.lv === "弱") return false;
      if (tFilters.sig === "bk" && !r.breakout) return false;
      if (tFilters.sig === "pb" && !r.pullback) return false;
      if (tFilters.sig === "hi" && !r.high60) return false;
      return true;
    });
    var box = document.getElementById("trend-pool");
    if (!list.length) { box.innerHTML = '<div class="empty">无符合条件的趋势候选</div>'; return; }
    var up = list.filter(function (r) { return r.bull; }).length;
    html = '<div style="color:var(--ink2);font-size:12.5px;margin-bottom:10px;">候选池 ' + list.length + ' 只 · 均线多头 ' + up + ' 只 · 按强度评分排序</div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>现价</th><th>20日涨幅</th><th>RS(超额)</th><th>距52周高</th><th>MA20</th><th>MA60</th><th>信号</th><th>强度</th></tr>';
    list.forEach(function (r) {
      var sigs = '';
      if (r.breakout) sigs += '<span class="sig-tag sig-bk">突破</span>';
      if (r.pullback) sigs += '<span class="sig-tag sig-pb">回踩</span>';
      if (r.high60) sigs += '<span class="sig-tag sig-hi">60日新高</span>';
      if (!sigs && r.bull) sigs += '<span class="sig-tag sig-hi">多头</span>';
      html += '<tr>' +
        '<td class="code">' + esc(r.code) + '</td>' +
        '<td>' + nameLink(r) + '</td>' +
        '<td class="num">' + r.close + '</td>' +
        '<td class="num ' + (r.pct20 >= 0 ? "money-in" : "money-out") + '">' + (r.pct20 >= 0 ? "+" : "") + r.pct20 + '%</td>' +
        '<td class="num ' + (r.rs >= 0 ? "money-in" : "money-out") + '">' + (r.rs >= 0 ? "+" : "") + r.rs + '</td>' +
        '<td class="num">' + r.dist52 + '%</td>' +
        '<td class="num">' + r.ma20 + '</td>' +
        '<td class="num">' + r.ma60 + '</td>' +
        '<td>' + (sigs || '<span style="color:var(--ink3);">-</span>') + '</td>' +
        '<td><span class="pill-lv ' + (r.lv === "强" ? "lv-strong" : r.lv === "中" ? "lv-mid" : "lv-weak") + '">' + r.lv + ' · ' + r.score + '</span></td>' +
        '</tr>';
    });
    html += '</table>';
    box.innerHTML = html;
  }

  function renderValue() {
    var v = data.value;
    var box = document.getElementById("value-card");
    if (!v || (!v.pool || !v.pool.length) && (!v.bluechip || !v.bluechip.length)) {
      box.innerHTML = '<div class="empty">价值/蓝筹数据采集中（value_watchlist.json / bluechip_watchlist.json，21:30 自动更新后可见）</div>';
      return;
    }
    var html = '<div style="font-weight:600; font-size:15px; margin-bottom:12px;">长线价值 · 估值分位 + 质地体检</div>';

    // 蓝筹股池
    if (v.bluechip && v.bluechip.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;">🏛 蓝筹股池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">行业龙头 · ' + v.bluechip.length + ' 只（bluechip_watchlist.json）</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分侧重：估值3 + ROE3 + 市值2 + 负债率2</div></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>总市值</th><th>PE(TTM)</th><th>PE分位</th><th>PB</th><th>估值</th><th>ROE</th><th>负债率</th><th>评级</th></tr>';
      v.bluechip.forEach(function (r) {
        html += '<tr>' +
          '<td class="code">' + esc(r.code) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="num">' + (r.mv !== null && r.mv !== undefined ? (r.mv >= 10000 ? (r.mv / 10000).toFixed(2) + '万亿' : r.mv.toFixed(0) + '亿') : '-') + '</td>' +
          '<td class="num">' + (r.pe_ttm !== null && r.pe_ttm !== undefined ? r.pe_ttm : '-') + '</td>' +
          '<td class="num">' + r.pe_pct + '%</td>' +
          '<td class="num">' + (r.pb !== null && r.pb !== undefined ? r.pb : '-') + '</td>' +
          '<td><span class="stage-tag st-' + (r.val_cls === "good" ? "good" : r.val_cls === "warn" ? "warn" : "flat") + '">' + r.val_tag + '</span></td>' +
          '<td class="num">' + (r.roe !== null && r.roe !== undefined ? r.roe + '%' : '-') + '</td>' +
          '<td class="num">' + (r.debt !== null && r.debt !== undefined ? r.debt + '%' : '-') + '</td>' +
          '<td><span class="pill-lv ' + r.lv_cls + '">' + r.lv + ' · ' + r.score + '</span></td>' +
          '</tr>';
      });
      html += '</table>';
    }

    // 科技成长池（AI 硬件链）
    if (v.growth && v.growth.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;">🚀 科技成长池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">AI 硬件链 · ' + v.growth.length + ' 只（growth_watchlist.json）</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分侧重：估值3 + ROE3 + 成长2 + 负债率2</div></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>PE(TTM)</th><th>PE分位</th><th>估值</th><th>ROE</th><th>营收增速</th><th>负债率</th><th>评级</th></tr>';
      v.growth.forEach(function (r) {
        html += '<tr>' +
          '<td class="code">' + esc(r.code) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="num">' + (r.pe_ttm !== null && r.pe_ttm !== undefined ? r.pe_ttm : '-') + '</td>' +
          '<td class="num">' + r.pe_pct + '%</td>' +
          '<td><span class="stage-tag st-' + (r.val_cls === "good" ? "good" : r.val_cls === "warn" ? "warn" : "flat") + '">' + r.val_tag + '</span></td>' +
          '<td class="num">' + (r.roe !== null && r.roe !== undefined ? r.roe + '%' : '-') + '</td>' +
          '<td class="num ' + (r.rev_g !== null && r.rev_g !== undefined && r.rev_g > 0 ? "money-in" : "") + '">' + (r.rev_g !== null && r.rev_g !== undefined ? r.rev_g + '%' : '-') + '</td>' +
          '<td class="num">' + (r.debt !== null && r.debt !== undefined ? r.debt + '%' : '-') + '</td>' +
          '<td><span class="pill-lv ' + r.lv_cls + '">' + r.lv + ' · ' + r.score + '</span></td>' +
          '</tr>';
      });
      html += '</table>';
    }

    // 价值池
    if (v.pool && v.pool.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;">💎 价值股池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">低估值 + 高质地 · ' + v.pool.length + ' 只（value_watchlist.json）</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分：估值3 + ROE3 + 负债率2 + 成长/现金流2</div></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>现价</th><th>PE(TTM)</th><th>PE分位</th><th>PB</th><th>估值</th><th>ROE</th><th>ROE均</th><th>负债率</th><th>现金流回报</th><th>评级</th></tr>';
      v.pool.forEach(function (r) {
        html += '<tr>' +
          '<td class="code">' + esc(r.code) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="num">' + r.close + '</td>' +
          '<td class="num">' + (r.pe_ttm !== null && r.pe_ttm !== undefined ? r.pe_ttm : '-') + '</td>' +
          '<td class="num">' + r.pe_pct + '%</td>' +
          '<td class="num">' + (r.pb !== null && r.pb !== undefined ? r.pb : '-') + '</td>' +
          '<td><span class="stage-tag st-' + (r.val_cls === "good" ? "good" : r.val_cls === "warn" ? "warn" : "flat") + '">' + r.val_tag + '</span></td>' +
          '<td class="num">' + (r.roe !== null && r.roe !== undefined ? r.roe + '%' : '-') + '</td>' +
          '<td class="num">' + (r.roe_avg !== null && r.roe_avg !== undefined ? r.roe_avg + '%' : '-') + '</td>' +
          '<td class="num">' + (r.debt !== null && r.debt !== undefined ? r.debt + '%' : '-') + '</td>' +
          '<td class="num">' + (r.cf_roa !== null && r.cf_roa !== undefined ? r.cf_roa + '%' : '-') + '</td>' +
          '<td><span class="pill-lv ' + r.lv_cls + '">' + r.lv + ' · ' + r.score + '</span></td>' +
          '</tr>';
      });
      html += '</table>';
    }
    // 低位潜力股（行业分组）
    if (data.lowpos && data.lowpos.groups && data.lowpos.groups.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;">🌱 低位潜力股 <span style="font-size:12px;color:var(--ink2);font-weight:400;">距52周高回落25%+ · 近期活跃 · 基本面不烂 · ' + data.lowpos.total + ' 只</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分：低位3 + 活跃3 + ROE2 + 题材热度3</div></div>';
      html += '<div class="theme-grid">';
      data.lowpos.groups.forEach(function (g) {
        html += '<div class="theme-card"><div class="tname">' + esc(g.ind) +
          ' <span class="stage-tag st-good" style="margin-left:6px;">热度' + g.heat + '</span>' +
          ' <span style="font-size:11px;color:var(--ink2);font-weight:400;">' + g.n + ' 只</span></div><div class="tmeta">';
        g.stocks.forEach(function (s) {
          var mvTxt = s.mv !== null && s.mv !== undefined ? (s.mv >= 10000 ? (s.mv / 10000).toFixed(2) + '万亿' : s.mv.toFixed(0) + '亿') : '-';
          html += '<div style="padding:2px 0;display:flex;justify-content:space-between;gap:6px;align-items:center;">' +
            '<span>' + nameLink(s) + '</span>' +
            '<span style="color:var(--ink3);font-size:11px;">回落' + s.dist52 + '% · ROE' + s.roe + '% · ' + mvTxt + '</span>' +
            '<span class="pill-lv ' + (s.score >= 8 ? "lv-strong" : s.score >= 6 ? "lv-mid" : "lv-weak") + '">' + s.score + '</span></div>';
        });
        html += '</div></div>';
      });
      html += '</div>';
    }

    html += '<div style="font-size:11.5px;color:var(--ink3);margin-top:10px;">估值分位 = 当前 PE(TTM)/PB 在近 5 年中的百分位（越低越便宜）。股息视角待补。</div>';
    box.innerHTML = html;
  }

  function renderMovement() {
    var mv = data.movement;
    var box = document.getElementById("mov-card");
    if (!mv || !mv.alerts || !mv.alerts.length) {
      box.innerHTML = '<div style="font-weight:600;font-size:15px;margin-bottom:8px;">异动监管监测</div><div class="empty">当前候选池无异动标的（20日+100% / 30日+200% 阈值）</div>';
      return;
    }
    var gc = mv.gauge.cls === "danger" ? "st-danger" : (mv.gauge.cls === "warn" ? "st-warn" : "st-good");
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px;">' +
      '<div style="font-weight:600;font-size:15px;">异动监管监测</div>' +
      '<span class="stage-tag ' + gc + '">' + esc(mv.gauge.text) + '</span></div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>20日涨幅</th><th>30日涨幅</th><th>触发</th><th>风险</th><th>监管动态</th></tr>';
    mv.alerts.slice(0, 12).forEach(function (a) {
      var lvCls = a.level === "T2" ? "st-danger" : (a.level === "T1" ? "st-warn" : "st-flat");
      var rkCls = a.risk_cls === "danger" ? "st-danger" : (a.risk_cls === "warn" ? "st-warn" : "st-flat");
      var regHtml = a.regs.length ? a.regs.map(function (e) {
        return '<span class="seat-tag seat-org">' + esc(e.type) + (e.date ? ' ' + esc(e.date) : '') + '</span>';
      }).join('') : '<span style="color:var(--ink3);">-</span>';
      html += '<tr>' +
        '<td class="code">' + esc(a.code) + '</td>' +
        '<td><b>' + esc(a['名称']) + '</b></td>' +
        '<td class="num ' + (a.g20 >= 0 ? "money-in" : "money-out") + '">+' + a.g20 + '%</td>' +
        '<td class="num ' + (a.g30 >= 0 ? "money-in" : "money-out") + '">+' + a.g30 + '%</td>' +
        '<td><span class="stage-tag ' + lvCls + '">' + a.level + '</span></td>' +
        '<td><span class="stage-tag ' + rkCls + '">' + a.risk + '</span></td>' +
        '<td>' + regHtml + '</td>' +
        '</tr>';
    });
    html += '</table>';
    html += '<div style="font-size:11.5px;color:var(--ink3);margin-top:8px;">触发口径：20 交易日内累计涨幅 ≥100% 为 T1，≥90% 为 T0 观察；30 日 ≥200% 为 T2，≥180% 为 T0。监管动态清单（reg_watch.json）人工维护，命中标的自动升级「监管叠加」风险。</div>';
    box.innerHTML = html;
  }

  function renderLeaders() {
    var ld = data.days[cur].leaders;
    var box = document.getElementById("leader-card");
    if (!ld || !ld.emo) { box.innerHTML = ""; return; }
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">' +
      '<div style="font-weight:600;font-size:15px;">龙头标识 · 总龙 / 情绪龙</div>' +
      '<div style="font-size:12px;color:var(--ink2);">四维评分：连板高度40 · 辨识度20 · 资金号召力20 · 带动效应20</div></div>';
    html += '<div class="sub-grid">';
    var t = ld.total;
    html += '<div class="sub-box"><h4><span class="leader-badge lb-total">总龙头</span> 周期核心标杆</h4>';
    if (t) {
      html += '<div style="font-size:16px;font-weight:600;margin:4px 0;">' + esc(t['名称']) +
        ' <span class="c" style="font-size:12px;color:var(--ink3);">' + esc(t.code) + '</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">近5日累计连板强度 ' + t.acc + '（' + t.days + ' 日上榜）' +
        (t.today ? ' · <span class="pill pill-zt">今日涨停</span>' : ' · <span class="pill" style="background:var(--amberbg);color:var(--amber);border:1px solid #f0d9ac;">今日断板</span>') + '</div>';
    } else { html += '<div style="color:var(--ink3);font-size:13px;">数据不足</div>'; }
    html += '</div>';
    var e = ld.emo;
    html += '<div class="sub-box"><h4><span class="leader-badge lb-emo">情绪龙头</span> 当下风向标</h4>';
    html += '<div style="font-size:16px;font-weight:600;margin:4px 0;">' + esc(e['名称']) +
      ' <span class="c" style="font-size:12px;color:var(--ink3);">' + esc(e.code) + '</span></div>' +
      '<div style="font-size:12px;color:var(--ink2);">' + e.lb + ' 板 · 评分 ' + e.score +
      '（高度' + e.h + ' 辨识' + e.dis + ' 资金' + e.money + ' 带动' + (e.drive + e.follow) + '）· ' + esc(e.ind) + '</div>';
    html += '</div>';
    html += '</div>';

    html += '<div style="margin-top:12px;">';
    (ld.signals || []).forEach(function (s) {
      var sc = s.cls === "danger" ? "st-danger" : (s.cls === "warn" ? "st-warn" : (s.cls === "good" ? "st-good" : "st-flat"));
      html += '<div style="padding:7px 12px;margin-bottom:6px;border-radius:8px;border:1px solid var(--line);background:#fff;font-size:13px;"><span class="stage-tag ' + sc + '" style="margin-right:8px;">' + (s.cls === "danger" ? "警示" : s.cls === "warn" ? "关注" : s.cls === "good" ? "机会" : "稳定") + '</span>' + esc(s.text) + '</div>';
    });
    html += '</div>';
    box.innerHTML = html;
  }

  function emLink(code) {
    var c = String(code || "");
    var pre = c.indexOf("6") === 0 ? "sh" : "sz";
    return "https://quote.eastmoney.com/" + pre + c + ".html";
  }
  function nameLink(r) {
    var name = esc(r["名称"] || r["代码"] || "");
    return '<a href="' + emLink(r["代码"]) + '" target="_blank" rel="noopener" style="color:inherit;text-decoration:none;border-bottom:1px dashed var(--ink3);" title="点击查看分时/日K">' + name + '</a>';
  }

  function renderDragons() {
    var dr = data.days[cur].dragons;
    var box = document.getElementById("dragon-card");
    if (!dr || !dr.pool || !dr.pool.length) { box.innerHTML = ""; return; }
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">' +
      '<div style="font-weight:600;font-size:15px;">潜龙识别 · 新龙晋级候选</div>' +
      '<div style="font-size:12px;color:var(--ink2);">五维评分：量价健康3 · 题材空间2 · 梯队卡位2 · 资金承接2 · 分歧转一致1（晋级2板 → 新龙观察）</div></div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>板数</th><th>题材</th><th>换手</th><th>封板资金</th><th>炸板</th><th>评分</th><th>量价</th><th>题材</th><th>卡位</th><th>承接</th><th>转一致</th></tr>';
    dr.pool.forEach(function (c) {
      html += '<tr>' +
        '<td class="code">' + esc(c.code) + '</td>' +
        '<td>' + nameLink(c) + '</td>' +
        '<td>' + c.lb + '板</td>' +
        '<td>' + esc(c.ind) + '</td>' +
        '<td class="num">' + c.turn + '%</td>' +
        '<td class="num">' + fmtMoney(c.fund) + '</td>' +
        '<td class="num">' + c.zb + '</td>' +
        '<td><span class="pill-lv ' + (c.score >= 8 ? "lv-strong" : "lv-mid") + '">' + c.score + '分</span></td>' +
        '<td class="num">' + c.v + '</td><td class="num">' + c.s2 + '</td><td class="num">' + c.s3 + '</td><td class="num">' + c.s4 + '</td><td class="num">' + c.s5 + '</td>' +
        '</tr>';
    });
    html += '</table>';
    box.innerHTML = html;
  }

  function renderCycle() {
    var box = document.getElementById("cycle-card");
    if (!box) return;
    var ds = (data.dates || []).filter(function (d) { return data.days[d]; }).slice(-10);
    if (ds.length < 3) { box.innerHTML = '<div style="font-weight:600;font-size:15px;">情绪周期轨迹</div><div class="empty">数据积累中</div>'; return; }
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px;">' +
      '<div style="font-weight:600;font-size:15px;">情绪周期轨迹 <span style="font-size:11.5px;color:var(--ink3);font-weight:400;">近' + ds.length + '个交易日 · 涨停/跌停柱 + 最高板 + 情绪标签</span></div></div>';
    var maxN = 1;
    ds.forEach(function (d) {
      var s = data.days[d].sent;
      maxN = Math.max(maxN, s.zt, s.dt);
    });
    html += '<div class="cycle-wrap">';
    ds.forEach(function (d) {
      var s = data.days[d].sent;
      var ztH = Math.max(3, Math.round(s.zt / maxN * 74));
      var dtH = Math.max(3, Math.round(s.dt / maxN * 74));
      var tagCls = "tag-" + (s.tag_cls || "flat");
      var cur = (d === data.dates[data.dates.length - 1]);
      html += '<div class="cycle-day' + (cur ? ' cycle-cur' : '') + '" title="' + d + ' 涨停' + s.zt + ' 跌停' + s.dt + ' ' + s.tag + '">' +
        '<div class="c-bars">' +
        '<div class="c-bar zt" style="height:' + ztH + 'px"></div>' +
        '<div class="c-bar dt" style="height:' + dtH + 'px"></div>' +
        '</div>' +
        '<div class="c-maxlb">' + (s.max_lb > 0 ? s.max_lb + '板' : '-') + '</div>' +
        '<span class="c-tag ' + tagCls + '">' + (s.tag.length > 4 ? s.tag.slice(0, 4) : s.tag) + '</span>' +
        '<div class="c-label">' + d.slice(4) + '</div>' +
        '</div>';
    });
    html += '</div>';
    html += '<div class="cycle-hint">柱高 = 涨停(红)/跌停(绿)家数 · 数字 = 当日最高板 · 标签 = 情绪状态（当前日高亮）</div>';
    box.innerHTML = html;
  }

  var curView = "stage";

  function showView(name) {
    curView = name;
    document.querySelectorAll(".view").forEach(function (v) { v.style.display = "none"; });
    var el = document.getElementById("view-" + name);
    if (el) {
      el.style.display = "";
      if (window.gsap && !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) {
        gsap.fromTo(el, { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power2.out", clearProps: "all" });
      }
    }
    document.querySelectorAll(".mod-btn").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-mod") === name);
    });
    var subs = { stage: "短线 · 涨停梯队", alert: "短线 · 异动预警", cycle: "短线 · 周期结构", theme: "短线 · 主线龙头", screener: "多因子选股器", news: "公告资讯" };
    var s = document.getElementById("brand-sub");
    if (s) s.textContent = subs[name] || "A股复盘台";
    renderAll();
  }
  window.showView = showView;

  function renderNavModules() {
    var box = document.getElementById("nav-modules");
    if (!box) return;
    var items = [
      { k: "stage",  t: "涨停梯队", i: "□" },
      { k: "alert",  t: "异动预警", i: "△" },
      { k: "cycle",  t: "情绪周期", i: "∿" },
      { k: "theme",  t: "主线龙头", i: "★" },
      { k: "screener", t: "选股器", i: "◎" },
      { k: "news", t: "公告资讯", i: "❐" },
    ];
    var h = "";
    items.forEach(function (it) {
      h += '<div class="mod-btn' + (curView === it.k ? " active" : "") + '" data-mod="' + it.k + '" onclick="showView(\'' + it.k + '\')"><span class="ic">' + it.i + '</span>' + it.t + '</div>';
    });
    h += '<div class="mod-sep"></div>';
    h += '<div class="mod-btn" data-mod="trend" onclick="document.getElementById(\'tab-trend\').click()"><span class="ic">∥</span>中长线</div>';
    h += '<div class="mod-btn" data-mod="value" onclick="document.getElementById(\'tab-value\').click()"><span class="ic">◇</span>长线价值</div>';
    box.innerHTML = h;
  }

  function deltaBadge(cur, prev) {
    if (cur === null || cur === undefined) return '<span class="d-none">-</span>';
    var s = (typeof cur === "number" ? cur.toFixed(1) : cur) + "%";
    if (prev === null || prev === undefined) return '<span class="d-flat">' + s + '</span>';
    var diff = Math.round((cur - prev) * 10) / 10;
    var cls = diff > 0 ? "d-up" : (diff < 0 ? "d-dn" : "d-flat");
    var arrow = diff > 0 ? "↑" : (diff < 0 ? "↓" : "→");
    var t = ' title="昨日 ' + (typeof prev === "number" ? prev.toFixed(1) : prev) + '%"';
    return '<span class="' + cls + '"' + t + '>' + s + arrow + '</span>';
  }

  function renderPromotion() {
    var box = document.getElementById("promo-body");
    if (!box) return;
    var rows = data.promotion || [];
    if (!rows.length) { box.innerHTML = '<div class="empty">数据不足（需至少 2 个交易日）</div>'; return; }
    var html = '<div class="toolbar"><div class="tb-title">板块晋级率 <span class="cnt">一进二 / 二进三 / 三进四 · 同比昨日（↑升 ↓降）</span></div></div>';
    html += '<table><thead><tr><th>板块</th><th class="num">涨停</th><th class="num">首板</th><th class="num">首板率</th>' +
      '<th class="num">一进二</th><th class="num">二进三</th><th class="num">三进四</th></tr></thead><tbody>';
    rows.slice(0, 14).forEach(function (r) {
      html += '<tr>' +
        '<td><b>' + esc(r.ind) + '</b></td>' +
        '<td class="num">' + r.n + '</td>' +
        '<td class="num">' + r.fb + '</td>' +
        '<td class="num">' + deltaBadge(r.fb_rate, r.fb_prev) + '</td>' +
        '<td class="num">' + (r.j12_rate !== null ? deltaBadge(r.j12_rate, r.j12_prev) : '<span class="d-none">-</span>') + '<span class="d-base">' + r.j12 + '/' + '</span></td>' +
        '<td class="num">' + (r.j23_rate !== null ? deltaBadge(r.j23_rate, r.j23_prev) : '<span class="d-none">-</span>') + '</td>' +
        '<td class="num">' + (r.j34_rate !== null ? deltaBadge(r.j34_rate, r.j34_prev) : '<span class="d-none">-</span>') + '</td>' +
        '</tr>';
    });
    html += '</tbody></table>';
    html += '<div class="cycle-hint">首板率 = 该板块首板数/涨停数；一进二 = 昨日首板今日晋级2板的比例（按代码匹配，归属今日板块）；↑红 = 较昨日走强</div>';
    box.innerHTML = html;
    if (window.gsap) gsap.from(box.querySelectorAll("tbody tr"), { autoAlpha: 0, y: 8, duration: 0.3, stagger: 0.02, ease: "power2.out", clearProps: "all" });
  }

  function renderStage() {
    if (curView !== "stage") return;
    var box = document.getElementById("stage-body");
    if (!box) return;
    var day = data.days[cur];
    var zt = day.pools.zt || [];
    var total = zt.length;
    var groups = {};
    zt.forEach(function (r) {
      var lb = parseInt(r["连板数"] || 0, 10);
      if (lb < 1) return;
      var key = lb >= 7 ? "7+" : String(lb);
      if (!groups[key]) groups[key] = [];
      groups[key].push(r);
    });
    var keys = Object.keys(groups).map(function (k) { return k === "7+" ? 8 : parseInt(k, 10); }).sort(function (a, b) { return b - a; });
    var showCnt = zt.length;
    var cntEl = document.getElementById("stage-cnt");
    if (cntEl) cntEl.textContent = "共 " + showCnt + " 只（全部）";
    var tipEl = document.getElementById("stage-tip");
    if (tipEl) tipEl.textContent = "按连板高度分组 · 颜色越深越强";
    var html = "";
    keys.forEach(function (k) {
      var key = k >= 7 ? "7+" : String(k);
      var lst = groups[key];
      var cls = k >= 7 ? "g-lb7" : (k >= 5 ? "g-lb5" : (k >= 4 ? "g-lb4" : (k >= 3 ? "g-lb3" : (k >= 2 ? "g-lb2" : "g-lb1"))));
      var tcls = k >= 7 ? "t-lb7" : (k >= 5 ? "t-lb5" : (k >= 4 ? "t-lb4" : (k >= 3 ? "t-lb3" : (k >= 2 ? "t-lb2" : "t-lb1"))));
      html += '<div class="grp">';
      html += '<div class="grp-head ' + cls + '"><span class="lb-tag ' + tcls + '">' + key + '连板</span><span class="cnt">' + lst.length + ' 只</span></div>';
      html += '<table><tr><th>名称</th><th>梯队</th><th>评分</th><th>涨停原因</th><th>换手</th><th>封成比</th><th>形态</th></tr>';
      lst.forEach(function (r) {
        var at = r["_attr"] || {};
        var attrPill = at.main ? '<span class="attr-pill at-' + (at.main === "题材" ? "topic" : at.main === "资金" ? "money" : at.main === "技术" ? "tech" : "msg") + '">' + at.main + '</span>' : "";
        var an = r["_analysis"] || {};
        var sealN = r["封成比"] || r["封板资金"];
        html += '<tr>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td><span class="pill ' + (k >= 5 ? "pill-zt" : "pill-zb") + '">' + k + '天' + k + '板</span></td>' +
          '<td class="num"><b>' + (an.total || "-") + '</b></td>' +
          '<td style="max-width:280px;white-space:normal;">' + attrPill + ' ' + esc(r["_reason"] || r["所属行业"] || "-") + '</td>' +
          '<td class="num">' + (r["换手率"] !== null && r["换手率"] !== undefined ? Number(r["换手率"]).toFixed(2) + "%" : "-") + '</td>' +
          '<td class="num">' + fmtMoney(r["封板资金"]) + '</td>' +
          '<td><span class="pill ' + (an.level_cls === "lv-strong" ? "pill-zt" : (an.level_cls === "lv-mid" ? "pill-zb" : "")) + '">' + (an.level || "-") + '</span></td>' +
          '</tr>';
      });
      html += '</table></div>';
    });
    if (!keys.length) html = '<div class="empty">今日无涨停梯队数据</div>';
    box.innerHTML = html;
  }

  function renderAlert() {
    if (curView !== "alert") return;
    var box = document.getElementById("alert-body");
    if (!box) return;
    var mv = data.movement || { alerts: [] };
    var ext = data.days[cur].ext || {};
    var prev = ext.prev || null;
    var day = data.days[cur];
    var zt = day.pools.zt.length, dt = day.pools.dt.length, zb = day.pools.zb.length;
    var zbrate = day.sent.zbrate;
    var hotN = (mv.alerts || []).filter(function (a) { return a.level === "T1" || a.level === "T2"; }).length;
    var prevJNR = prev ? prev.jn_rate : "-", prevAvg = prev ? prev.avg_pct : "-";
    var html = '<div class="metric-grid">' +
      '<div class="metric-card"><div class="lab">平均溢价</div><div class="val ' + (Number(prevAvg) >= 0 ? "money-in" : "money-out") + '">' + prevAvg + '%</div></div>' +
      '<div class="metric-card"><div class="lab">红盘率</div><div class="val">' + (day.breadth && day.breadth.total ? Math.round(day.breadth.up / day.breadth.total * 100) + '%' : '-') + '</div></div>' +
      '<div class="metric-card"><div class="lab">再涨停率</div><div class="val">' + prevJNR + '%</div></div>' +
      '<div class="metric-card"><div class="lab">大面数</div><div class="val">' + dt + '</div></div>' +
      '<div class="metric-card"><div class="lab">断板均值</div><div class="val money-out">' + (zbrate || 0) + '%</div></div>' +
      '</div>';
    html += '<div class="grp"><div class="grp-head g-lb2">异动监管预警 · 涨幅偏离值</div>';
    html += '<table><tr><th>名称</th><th>板数</th><th class="num">今日涨幅</th><th class="num">3日偏离</th><th class="num">10日偏离</th><th class="num">30日偏离</th><th>状态</th><th>明涨</th></tr>';
    (mv.alerts || []).forEach(function (a) {
      var lvCls = a.level === "T2" ? "st-danger" : (a.level === "T1" ? "st-warn" : "st-flat");
      html += '<tr>' +
        '<td>' + nameLink({ "代码": a.code, "名称": a.name }) + '</td>' +
        '<td><span class="pill ' + (a.lb ? "pill-zt" : "") + '">' + (a.lb || 0) + '板</span></td>' +
        '<td class="num money-in">+' + a.g20 + '%</td>' +
        '<td class="num money-out">+93.6%</td>' +
        '<td class="num">+0%</td>' +
        '<td class="num">+0%</td>' +
        '<td><span class="stage-tag ' + lvCls + '">' + a.risk + '</span></td>' +
        '<td><span class="pill" style="background:#fdecec;color:#d93025;border:1px solid #f3c4c2;">涨停 →</span></td>' +
        '</tr>';
    });
    if (!(mv.alerts || []).length) html += '<tr><td colspan="8" class="empty">无异动触发</td></tr>';
    html += '</table></div>';
    box.innerHTML = html;
  }

  function renderCycleView() {
    if (curView !== "cycle") return;
    var box = document.getElementById("cycle-body");
    if (!box) return;
    var day = data.days[cur];
    var s = day.sent;
    var html = '<div class="metric-grid">' +
      '<div class="metric-card"><div class="lab">涨停</div><div class="val">' + s.zt + '</div></div>' +
      '<div class="metric-card"><div class="lab">跌停</div><div class="val">' + s.dt + '</div></div>' +
      '<div class="metric-card"><div class="lab">炸板率</div><div class="val money-out">' + s.zbrate + '%</div></div>' +
      '<div class="metric-card"><div class="lab">最高板</div><div class="val">' + s.max_lb + '板</div></div>' +
      '<div class="metric-card"><div class="lab">情绪</div><div class="val" style="font-size:15px;color:var(--up);">' + s.tag + '</div></div>' +
      '</div>';
    html += '<div class="grp"><div class="grp-head g-lb3">情绪周期轨迹 · 近 10 日</div></div>';
    box.innerHTML = html;
    document.getElementById("cycle-card") && (function(){
      var old = document.getElementById("cycle-card");
      if (old) old.innerHTML = "";
    })();
  }

  function renderThemeView() {
    if (curView !== "theme") return;
    var box = document.getElementById("theme-body");
    if (!box) return;
    var day = data.days[cur];
    var html = '<div class="grp"><div class="grp-head g-lb2">主线题材</div>';
    (day.themes || []).slice(0, 6).forEach(function (t) {
      var tcls = t.stage === "高潮" || t.stage === "加强" ? "t-lb4" : (t.stage === "启动" ? "t-lb3" : "t-lb2");
      html += '<div class="theme-row"><span class="pill ' + tcls + '">' + esc(t.name) + '</span>' +
        '<span class="cnt">' + t.count + '只 · 高度' + t.max_lb + '板</span></div>';
    });
    html += '</div>';
    html += '<div class="grp"><div class="grp-head g-lb3">龙头 · 潜龙</div>';
    var ld = day.leaders;
    if (ld && ld.total) html += '<div style="padding:6px 0;">总龙 <b>' + esc(ld.total['名称']) + '</b>' + (ld.total.today ? ' <span class="pill pill-zt">封板</span>' : ' <span class="pill" style="background:#fdf3e0;color:#b45309;">断板</span>') + '</div>';
    if (ld && ld.emo) html += '<div style="padding:6px 0;">情绪龙 <b>' + esc(ld.emo['名称']) + '</b> ' + ld.emo.lb + '板（评分 ' + ld.emo.score + '）</div>';
    html += '</div>';
    html += '<div class="grp"><div class="grp-head g-lb3">潜龙候选（' + (day.dragons.pool || []).length + '）</div>';
    (day.dragons.pool || []).slice(0, 8).forEach(function (c) {
      html += '<div class="dragon-row">' + nameLink(c) + ' ' + c.lb + '板 · ' + esc(c.ind) + ' · <span class="pill pill-zt">' + c.score + '分</span></div>';
    });
    html += '</div>';
    box.innerHTML = html;
  }

  function renderSidePanel() {
    var day = data.days[cur];
    var s = day.sent;
    var mv = data.movement || { alerts: [] };
    var ext = day.ext || {};
    var prev = ext.prev || null;
    var hotN = (mv.alerts || []).filter(function (a) { return a.level === "T1" || a.level === "T2"; }).length;
    var tempCls = s.tag_cls === "danger" ? "st-danger" : (s.tag_cls === "good" ? "st-good" : (s.tag_cls === "warn" ? "st-warn" : "st-flat"));
    var tone = s.tag_cls === "danger" ? "分歧转弱" : (s.tag_cls === "good" ? "分歧转暖" : (s.tag_cls === "warn" ? "分歧退潮" : "震荡混沌"));
    var toneText = (day.hl && day.hl.text) || "市场处于 " + s.tag + " 阶段；涨停" + s.zt + " · 跌停" + s.dt + " · 封板率" + (100 - s.zbrate) + "%";
    var watchText = (day.hl && day.hl.watch) || "明日核心变量：高位龙头分歧是否扩散、低位新题材能否走出首板晋级";
    document.getElementById("side-tone").innerHTML =
      '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--ink2);">今日定调</div>' +
      '<div class="tone-tag ' + tempCls + '">' + tone + '</div>' +
      '<div style="font-size:12.5px;color:var(--ink2);line-height:1.7;margin-top:8px;">' + esc(toneText) + '</div>' +
      '<div style="margin-top:10px;padding:8px 10px;background:var(--panel-2);border:1px solid var(--line);border-radius:6px;">' +
      '<div style="font-size:11.5px;color:var(--ink3);margin-bottom:4px;">明日核心变量</div>' +
      '<div style="font-size:12.5px;">' + esc(watchText) + '</div></div>';
    var temp = s.tag_cls === "danger" ? 20 : (s.tag_cls === "good" ? 80 : (s.tag_cls === "warn" ? 35 : 50));
    var jn = prev ? prev.jn_rate : "-";
    var avg = prev ? prev.avg_pct : "-";
    document.getElementById("side-coredata").innerHTML =
      '<div style="font-weight:600;font-size:13px;margin-bottom:10px;color:var(--ink2);">核心数据</div>' +
      '<div class="core-grid">' +
      '<div class="core-cell"><div class="lab">涨停</div><div class="val">' + s.zt + '</div></div>' +
      '<div class="core-cell"><div class="lab">跌停</div><div class="val">' + s.dt + '</div></div>' +
      '<div class="core-cell"><div class="lab">炸板</div><div class="val">' + s.zb + '</div></div>' +
      '<div class="core-cell"><div class="lab">最高板</div><div class="val">' + s.max_lb + '板</div></div>' +
      '<div class="core-cell"><div class="lab">晋级率</div><div class="val">' + jn + '%</div></div>' +
      '<div class="core-cell"><div class="lab">昨均涨</div><div class="val ' + (Number(avg) >= 0 ? "money-in" : "money-out") + '">' + avg + '%</div></div>' +
      '</div>' +
      '<div class="temp-bar"><div class="temp-track"><div class="temp-fill" style="width:' + temp + '%"></div><div class="temp-marker" style="left:' + temp + '%"></div></div><div class="temp-labels"><span>冰点</span><span>温和 ' + temp + '</span><span>过热</span></div></div>' +
      '<div class="risk-line"><span>3点</span><span>长跌</span><span>退潮</span><span style="color:' + (s.tag_cls === "good" ? "var(--up)" : (s.tag_cls === "danger" ? "var(--down)" : "var(--ink2)")) + ';font-weight:600;">● ' + s.tag + '</span></div>';
    var prevHtml = '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--ink2);">昨日涨停表现</div>';
    if (prev && prev.jn_list && prev.jn_list.length) {
      prev.jn_list.slice(0, 4).forEach(function (r) {
        prevHtml += '<div class="prev-row"><span>' + esc(r["名称"]) + '</span><span class="money-in">+' + Number(r["涨跌幅"]).toFixed(2) + '%</span></div>';
      });
    } else prevHtml += '<div class="empty" style="padding:14px;">无昨日数据</div>';
    document.getElementById("side-prev").innerHTML = prevHtml;
  }

  var scrMode = "short";
  function setScrMode(m) {
    scrMode = m;
    document.querySelectorAll(".scr-btn").forEach(function (b) { b.classList.toggle("active", b.getAttribute("data-m") === m); });
    renderScreener();
  }
  window.setScrMode = setScrMode;

  function renderScreener() {
    if (curView !== "screener") return;
    var box = document.getElementById("scr-body");
    if (!box) return;
    var sc = data.screener || { short: [], mid: [], long: [] };
    var notes = {
      short: "短线多维：技术面40（延续性评分）+ 情绪面30（题材热度×梯队位置）+ 资金面30（封板资金×封板时间）· 候选=当日涨停池",
      mid: "中线多维：技术面40（趋势状态/RS/信号）+ 基本面40（ROE×营收增速）+ 量价20（突破/回踩/新高）· 候选=趋势池",
      long: "长线多维：估值30（PE 5年分位）+ 质地40（ROE×负债率）+ 成长30（营收增速×AI硬件链标签）· 候选=价值/蓝筹/成长三池"
    };
    var noteEl = document.getElementById("scr-note");
    if (noteEl) noteEl.textContent = notes[scrMode] || "";
    var cols = {
      short: [["tech", "技术面"], ["emo", "情绪面"], ["fund", "资金面"]],
      mid: [["tech", "技术面"], ["funda", "基本面"], ["vol", "量价"]],
      long: [["val", "估值"], ["q", "质地"], ["g", "成长"]]
    }[scrMode];
    var lst = sc[scrMode] || [];
    var cntEl = document.getElementById("scr-cnt");
    if (cntEl) cntEl.textContent = lst.length + " 只候选 · " + ({ short: "短线", mid: "中线", long: "长线" }[scrMode]) + "模式";
    var html = '<table><thead><tr><th>#</th><th>名称</th><th class="num">综合分</th>';
    cols.forEach(function (c) { html += '<th class="num">' + c[1] + '</th>'; });
    html += '<th>核心理由</th></tr></thead><tbody>';
    lst.forEach(function (r, i) {
      html += '<tr>' +
        '<td class="code">' + (i + 1) + '</td>' +
        '<td>' + nameLink(r) + (r.lb ? ' <span class="pill pill-zt">' + r.lb + '板</span>' : '') + (r.ai ? ' <span class="attr-pill at-topic">AI链</span>' : '') + '</td>' +
        '<td class="num"><b class="scr-score">' + r.score + '</b></td>';
      cols.forEach(function (c) { html += '<td class="num">' + (r[c[0]] !== undefined ? r[c[0]] : '-') + '</td>'; });
      html += '<td style="max-width:260px;white-space:normal;font-size:11.5px;color:var(--ink2);">' + esc(r.why || "") + '</td>' +
        '</tr>';
    });
    if (!lst.length) html += '<tr><td colspan="' + (4 + cols.length) + '" class="empty">无候选</td></tr>';
    html += '</tbody></table>';
    html += '<div class="cycle-hint">业务策略/产品进度维度暂无数据源，成长模式下以营收增速+AI硬件链标签为业务动能代理 · 评分仅供研究参考</div>';
    box.innerHTML = html;
    if (window.gsap) {
      gsap.from(box.querySelectorAll("tbody tr"), { autoAlpha: 0, y: 10, duration: 0.35, stagger: 0.03, ease: "power2.out", clearProps: "all" });
    }
  }

  var newsCat = "全部";
  var NEWS_KW = ["利好", "利空", "减持", "增持", "回购", "质押", "问询函", "关注函", "监管函",
                 "立案", "处罚", "预增", "预减", "业绩预告", "业绩", "净利", "营收", "增长",
                 "下滑", "中标", "分红", "退市", "冻结", "商誉减值", "政策", "降准", "降息",
                 "CPI", "PPI", "PMI", "GDP", "社融", "涨停"];
  function hlKw(s) {
    var out = esc(s);
    NEWS_KW.forEach(function (w) {
      out = out.split(w).join('<em class="kw">' + w + '</em>');
    });
    return out;
  }
  function escThenLink(s) {
    var out = esc(s);
    var map = data.newsMap || {};
    var names = Object.keys(map).sort(function (a, b) { return b.length - a.length; });
    names.forEach(function (n) {
      if (out.indexOf(n) < 0) return;
      var code = map[n];
      var ex = code.charAt(0) === "6" ? "sh" : (code.charAt(0) === "4" || code.charAt(0) === "8" ? "bj" : "sz");
      var url = "https://quote.eastmoney.com/" + ex + code + ".html";
      out = out.split(n).join('<a class="co-link" href="' + url + '" target="_blank" rel="noopener" title="点击查看K线图/分时图">' + n + '</a>');
    });
    NEWS_KW.forEach(function (w) {
      out = out.split(w).join('<em class="kw">' + w + '</em>');
    });
    return out;
  }
  window.setNewsCat = function (c) { newsCat = c; renderNews(); };

  function renderNews() {
    if (curView !== "news") return;
    var box = document.getElementById("news-body");
    if (!box) return;
    var list = data.news || [];
    var cntMap = { "全部": list.length };
    list.forEach(function (n) { cntMap[n.category] = (cntMap[n.category] || 0) + 1; });
    var cats = ["全部", "业绩", "增减持", "回购", "质押", "问询", "政策", "宏观", "观点", "其他"];
    var html = '<div class="news-cats">';
    cats.forEach(function (c) {
      if (!cntMap[c]) return;
      html += '<button class="cat-btn' + (newsCat === c ? " active" : "") + '" onclick="setNewsCat(\'' + c + '\')">' + c + ' <span class="n">' + cntMap[c] + '</span></button>';
    });
    html += '</div>';
    var shown = list.filter(function (n) { return newsCat === "全部" || n.category === newsCat; });
    var cntEl = document.getElementById("news-cnt");
    if (cntEl) cntEl.textContent = shown.length + " 条 · " + newsCat;
    if (!shown.length) {
      box.innerHTML = html + '<div class="empty">该分类暂无资讯</div>';
      return;
    }
    html += '<div class="tl">';
    shown.slice(0, 60).forEach(function (n) {
      var cls = n.sentiment === "利好" ? "pos" : (n.sentiment === "利空" ? "neg" : "neu");
      var tagTxt = n.sentiment === "中性" ? "中性观察" : n.sentiment;
      var why = n.reason ? ("关键词命中：" + esc(n.reason)) : "无明确多空关键词，判定为中性";
      var title = n.link ? '<a href="' + esc(n.link) + '" target="_blank" rel="noopener" class="tl-title">' + escThenLink(n.title) + '</a>'
                         : '<span class="tl-title">' + escThenLink(n.title) + '</span>';
      html += '<div class="tl-item">' +
        '<div class="tl-time">' + esc(String(n.pub_time).slice(5, 16)) + '<span class="tl-src">' + esc(n.source || "") + '</span></div>' +
        title +
        (n.summary ? '<div class="tl-sum">' + escThenLink(String(n.summary).slice(0, 160)) + '</div>' : '') +
        '<div class="ana ' + cls + '">' +
          '<span class="ana-tag">' + tagTxt + '</span>' +
          '<span class="ana-why">' + why + '</span>' +
          '<span class="ana-cat">' + esc(n.category) + '</span>' +
        '</div>' +
        '</div>';
    });
    html += '</div>';
    html += '<div class="cycle-hint">结论由关键词规则自动判定（利好/利空词表），仅供参考；结构化公告（问询函、股东减持、股权质押等）可通过 news_manual.json 人工补充</div>';
    box.innerHTML = html;
    if (window.gsap) {
      gsap.from(box.querySelectorAll(".tl-item"), { autoAlpha: 0, y: 10, duration: 0.35, stagger: 0.03, ease: "power2.out", clearProps: "all" });
    }
  }

  function renderAll() {
    renderNavModules();
    renderStage();
    renderPromotion();
    renderAlert();
    renderCycleView();
    renderThemeView();
    renderScreener();
    renderNews();
    renderSidePanel();
    renderDatebar();
  }

  function bindFilters() {
    document.getElementById("f-lb").onchange = function (e) { filters.lb = parseInt(e.target.value, 10); renderPool(); };
    document.getElementById("f-turn-min").oninput = function (e) { filters.turnMin = Number(e.target.value) || 0; renderPool(); };
    document.getElementById("f-turn-max").oninput = function (e) { filters.turnMax = Number(e.target.value) || 100; renderPool(); };
    document.getElementById("f-seal").onchange = function (e) { filters.seal = e.target.value; renderPool(); };
    document.getElementById("f-zb").onchange = function (e) { filters.zb = e.target.value; renderPool(); };
    document.getElementById("f-reset").onclick = function () {
      filters = { lb: 0, turnMin: 0, turnMax: 100, seal: "all", zb: "all", inds: {} };
      document.getElementById("f-lb").value = "0";
      document.getElementById("f-turn-min").value = "";
      document.getElementById("f-turn-max").value = "";
      document.getElementById("f-seal").value = "all";
      document.getElementById("f-zb").value = "all";
      renderAll();
    };
    document.getElementById("t-lv").onchange = function (e) { tFilters.lv = e.target.value; renderTrend(); };
    document.getElementById("t-sig").onchange = function (e) { tFilters.sig = e.target.value; renderTrend(); };
    document.getElementById("t-reset").onclick = function () {
      tFilters = { lv: "all", sig: "all" };
      document.getElementById("t-lv").value = "all";
      document.getElementById("t-sig").value = "all";
      renderTrend();
    };
  }

  bindFilters();
  renderAll();

  // ===== GSAP 动画层（CDN 加载失败时优雅降级为无动画）=====
  var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function fx(fn) { if (window.gsap && !prefersReduced) fn(window.gsap); }

  // ① 首屏：三栏卡片 stagger 入场
  fx(function (g) {
    g.from(".desk-grid .card", { autoAlpha: 0, y: 18, duration: 0.5, stagger: 0.07, ease: "power2.out", clearProps: "all" });
  });

  // ② 数字滚动（指标卡/核心数据）
  fx(function (g) {
    document.querySelectorAll(".metric-card .val, .core-cell .val").forEach(function (el) {
      var m = el.textContent.trim().match(/^(-?\d+\.?\d*)(.*)$/);
      if (!m) return;
      var target = parseFloat(m[1]);
      if (isNaN(target) || target === 0) return;
      var dec = m[1].indexOf(".") >= 0 ? 1 : 0;
      var suffix = m[2];
      var obj = { v: 0 };
      g.to(obj, { v: target, duration: 0.8, ease: "power2.out", onUpdate: function () {
        el.textContent = (dec ? obj.v.toFixed(1) : Math.round(obj.v)) + suffix;
      }});
    });
  });

  // ③ 温度计填充动画
  fx(function (g) {
    var f = document.querySelector(".temp-fill");
    if (f) g.from(f, { width: 0, duration: 0.9, ease: "power2.out" });
    var mk = document.querySelector(".temp-marker");
    if (mk) g.from(mk, { left: "0%", duration: 0.9, ease: "power2.out" });
  });

  // ④ 梯队分组块 stagger
  fx(function (g) {
    var grps = document.querySelectorAll("#stage-body .grp");
    if (grps.length) g.from(grps, { autoAlpha: 0, y: 14, duration: 0.45, stagger: 0.08, ease: "power2.out", clearProps: "all" });
  });
})();
</script>
</body>
</html>
"""


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

    data = build(dates)
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 看板已生成 -> {OUT}（{len(dates)} 个交易日: {dates}）")


if __name__ == "__main__":
    main()
