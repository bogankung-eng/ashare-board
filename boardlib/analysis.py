# -*- coding: utf-8 -*-
"""分析函数层（P11b 拆分，逐字节搬运自 _gen_board.py）。"""
import json
import os
import sqlite3
from datetime import datetime

from .config import BASE, DB, OUT, IDX

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
        # P7: 优先真实涨停原因（同花顺揭秘），回退"行业·家数"
        r["_reason"] = str(r["涨停原因"]) if r.get("涨停原因") else f"{ind}·{ind_count[ind]}家"
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
    """题材聚类 + 阶段判断 + 高低切 v0
    P7 升级：优先真实涨停原因（同花顺揭秘，按首标签聚类）；覆盖率 <50% 回退行业聚合。"""
    zt = pools["zt"]
    has_reason = [r for r in zt if r.get("涨停原因")]
    use_reason = len(zt) > 0 and len(has_reason) / len(zt) >= 0.5

    def _key(r):
        if use_reason and r.get("涨停原因"):
            return str(r["涨停原因"]).split("+")[0].strip() or (r.get("所属行业") or "其他")
        return r.get("所属行业") or "其他"

    groups = {}
    for r in zt:
        groups.setdefault(_key(r), []).append(r)
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
            "src": "reason" if use_reason else "industry",
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
        # P7: 按昨日连板数分组反馈矩阵（借鉴 Vibe-Astock feedback_matrix）
        grp = {}
        for r in prev:
            lb = int(_f(r, "昨日连板数"))
            k = "1" if lb <= 1 else ("2" if lb == 2 else "3+")
            g = grp.setdefault(k, {"base": 0, "jn": 0, "red": 0, "pct": 0.0})
            g["base"] += 1
            px, ztpx = _f(r, "最新价"), _f(r, "涨停价")
            if ztpx > 0 and abs(px - ztpx) / ztpx < 0.001:
                g["jn"] += 1
            if _f(r, "涨跌幅") > 0:
                g["red"] += 1
            g["pct"] += _f(r, "涨跌幅")
        matrix = []
        for k, label in (("1", "昨日首板"), ("2", "昨日2板"), ("3+", "昨日3板+")):
            g = grp.get(k)
            if not g:
                continue
            matrix.append({
                "lb": label, "base": g["base"], "jn": g["jn"], "red": g["red"],
                "jn_rate": round(g["jn"] / g["base"] * 100, 1),
                "red_rate": round(g["red"] / g["base"] * 100, 1),
                "avg_pct": round(g["pct"] / g["base"], 2),
            })
        out["prev"] = {
            "total": len(prev), "jn": len(jn), "db": len(db),
            "jn_rate": round(len(jn) / len(prev) * 100, 1) if prev else 0,
            "avg_pct": round(avg, 2),
            "jn_list": sorted(jn, key=lambda x: -_f(x, "涨跌幅"))[:12],
            "db_list": sorted(db, key=lambda x: -_f(x, "涨跌幅"))[:12],
            "matrix": matrix,
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


def analyze_seal_time(pools):
    """P9: 首次封板时间五桶分布（借鉴 Vibe-Astock 封板结构维度）。
    竞价+早盘封板占比高 = 承接强/情绪强；尾盘占比高 = 偷袭板/封板质量弱。
    数据源：涨停池"首次封板时间"（akshare HHMMSS 六位字符串），历史全量可用。"""
    cnt = {"竞价": 0, "早盘": 0, "上午": 0, "下午": 0, "尾盘": 0}
    for r in pools["zt"]:
        t = str(r.get("首次封板时间") or "")
        if len(t) != 6 or not t.isdigit():
            continue
        v = int(t[:4])
        if v <= 925:
            cnt["竞价"] += 1
        elif v < 1000:
            cnt["早盘"] += 1
        elif v <= 1130:
            cnt["上午"] += 1
        elif v < 1430:
            cnt["下午"] += 1
        else:
            cnt["尾盘"] += 1
    total = sum(cnt.values())
    if not total:
        return None
    return {
        "total": total,
        "buckets": [{"label": k, "n": v, "pct": round(v / total * 100)}
                    for k, v in cnt.items()],
        "early_pct": round((cnt["竞价"] + cnt["早盘"]) / total * 100),
        "late_pct": round(cnt["尾盘"] / total * 100),
    }


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


def fetch_quotes(codes):
    """批量行情：code -> {name, pct}。腾讯单请求 → 新浪备源 → 当日缓存兜底。
    腾讯对同 IP 高频返回空 body（HTTP 200），故合并为一次请求并落缓存。"""
    out = {}
    if not codes:
        return out

    def pref(c):
        c = str(c)
        if c[:2] in ("sh", "sz", "bj"):
            return c
        if c and c[0] == "6":
            return "sh" + c
        if c and c[0] in ("0", "3"):
            return "sz" + c
        return "bj" + c if c and c[0] in ("4", "8", "9") else "sz" + c

    def save_cache():
        try:
            cpath = os.path.join(BASE, "data", "quotes_cache.json")
            if out:
                out["_date"] = datetime.now().strftime("%Y%m%d")
                json.dump(out, open(cpath, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass

    def load_cache():
        try:
            cpath = os.path.join(BASE, "data", "quotes_cache.json")
            if os.path.exists(cpath):
                cached = json.load(open(cpath, encoding="utf-8"))
                if cached.get("_date") == datetime.now().strftime("%Y%m%d"):
                    cached.pop("_date", None)
                    out.update(cached)
        except Exception:
            pass

    try:
        import urllib.request
        pcs = sorted({pref(c) for c in codes})
        # ① 腾讯：一次请求全部
        try:
            url = "https://qt.gtimg.cn/q=" + ",".join(pcs)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "ignore")
            for line in raw.split(";"):
                if '="' not in line or "~" not in line:
                    continue
                key, body = line.split('="', 1)
                f = body.rstrip('"\n').split("~")
                if key.startswith(("v_sh", "v_sz", "v_bj")) and len(f) > 32 and f[1]:
                    try:
                        pct = float(f[32])
                    except Exception:
                        pct = None
                    out[key[6:]] = {"name": f[1], "pct": pct}
        except Exception:
            pass
        # ② 新浪备源（补腾讯缺失）
        if len(out) < len(pcs):
            try:
                url2 = "https://hq.sinajs.cn/list=" + ",".join(pcs)
                req2 = urllib.request.Request(url2, headers={
                    "User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"})
                raw2 = urllib.request.urlopen(req2, timeout=15).read().decode("gbk", "ignore")
                for line in raw2.splitlines():
                    if 'hq_str_' not in line or '="' not in line:
                        continue
                    key, body = line.split('="', 1)
                    f = body.rstrip('";').split(",")
                    code = key.replace("var hq_str_", "")
                    if len(f) > 3 and f[0]:
                        try:
                            price, prev = float(f[3]), float(f[2])
                            pct = round((price / prev - 1) * 100, 2) if prev > 0 else None
                        except Exception:
                            pct = None
                        out[code[2:]] = {"name": f[0], "pct": pct}
            except Exception:
                pass
    except Exception:
        pass
    if out:
        save_cache()
    else:
        load_cache()
    return out


NAMEPLAY_STOP = {"股", "份", "集", "团"}


def _pool_lb_stat(stat):
    """涨停统计 '6/4'（天/板）→ 板数 4；解析失败按 1 板"""
    try:
        return int(str(stat).split("/")[1])
    except Exception:
        return 1


def _hhmm_to_min(t, default="150000"):
    """'092500' → 565 分钟"""
    s = str(t or default)
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:2]) * 60 + int(s[2:4])
    return 900


def analyze_day_timeline(days, dates):
    """当日时间线：上板事件流（情绪）· 板块启动顺序（强弱）· 高标炸板→他板上板（节点转换）"""
    if not dates:
        return {"events": [], "nodes": [], "inds": [], "n_up": 0, "n_zb": 0, "max_lb": 0}
    day = days[dates[-1]]
    zt, zb = day["pools"]["zt"], day["pools"]["zb"]
    ups, downs = [], []
    for r in zt:
        ups.append({"code": r.get("代码"), "name": r.get("名称"),
                    "ind": r.get("所属行业") or "其他",
                    "lb": int(r.get("连板数") or 0), "t": _hhmm_to_min(r.get("首次封板时间")),
                    "turn": float(r.get("换手率") or 0), "zbcnt": 0, "kind": "up",
                    "reason": str(r.get("涨停原因") or "").split("+")[0][:16]})
    for r in zb:
        downs.append({"code": r.get("代码"), "name": r.get("名称"),
                      "ind": r.get("所属行业") or "其他",
                      "lb": _pool_lb_stat(r.get("涨停统计")), "t": _hhmm_to_min(r.get("首次封板时间")),
                      "turn": float(r.get("换手率") or 0),
                      "zbcnt": max(int(r.get("炸板次数") or 1), 1), "kind": "zb"})
    events = sorted(ups + downs, key=lambda e: e["t"])
    max_lb = max((u["lb"] for u in ups), default=0)
    # 高标炸板：板数≥3 或 达当日最高板（炸板池板数按涨停统计回溯）
    high_zb = [z for z in downs if z["lb"] >= 3 or (max_lb and z["lb"] >= max_lb)]
    # 节点转换：高标炸板后 10 分钟内、他板块个股上板
    nodes = []
    for z in sorted(high_zb, key=lambda e: e["t"]):
        after = [u for u in ups
                 if z["t"] <= u["t"] <= z["t"] + 10 and u["ind"] != z["ind"]]
        if after:
            nodes.append({"zb": z, "after": after[:3]})
    # 板块启动顺序（强弱）：按板块首板时间
    ind_m = {}
    for u in ups:
        m = ind_m.setdefault(u["ind"], {"ind": u["ind"], "first": u["t"], "n": 0, "maxlb": 0})
        m["n"] += 1
        m["maxlb"] = max(m["maxlb"], u["lb"])
        m["first"] = min(m["first"], u["t"])
    inds = sorted(ind_m.values(), key=lambda m: (m["first"], -m["n"]))
    return {"date": dates[-1], "events": events, "nodes": nodes, "inds": inds,
            "n_up": len(ups), "n_zb": len(downs), "max_lb": max_lb}


def analyze_period_timeline(days, dates, n):
    """周/月时间线：每日情绪柱 + 板块热力矩阵 + 关键节点（新高/断层/冰点/高潮）"""
    dd = dates[-n:]
    if not dd:
        return {"days": [], "nodes": [], "matrix": [], "dates": []}
    days_arr = []
    for d in dd:
        day = days[d]
        zt, zb, dt = day["pools"]["zt"], day["pools"]["zb"], day["pools"]["dt"]
        lbs = [int(r.get("连板数") or 0) for r in zt]
        days_arr.append({"date": d, "zt": len(zt), "dt": len(dt), "zb": len(zb),
                         "maxlb": max(lbs) if lbs else 0})
    nodes, prev_max = [], 0
    for i, e in enumerate(days_arr):
        if e["maxlb"] > prev_max and e["maxlb"] >= 4:
            nodes.append({"date": e["date"], "type": "high", "txt": f"空间板新高 {e['maxlb']}板"})
        elif prev_max and e["maxlb"] <= prev_max - 2:
            nodes.append({"date": e["date"], "type": "break", "txt": f"高度断层 {prev_max}板→{e['maxlb']}板"})
        prev_max = max(prev_max, e["maxlb"])
        if i >= 3:
            avg = sum(x["zt"] for x in days_arr[i - 3:i]) / 3
            if e["zt"] < avg * 0.55:
                nodes.append({"date": e["date"], "type": "ice",
                              "txt": f"涨停冰点 {e['zt']}家（前3日均 {avg:.0f}）"})
            elif e["zt"] > avg * 1.6:
                nodes.append({"date": e["date"], "type": "hot",
                              "txt": f"涨停高潮 {e['zt']}家（前3日均 {avg:.0f}）"})
    ind_stat = {}
    for d in dd:
        for r in days[d]["pools"]["zt"]:
            ind = r.get("所属行业") or "其他"
            ind_stat.setdefault(ind, {})
            ind_stat[ind][d] = ind_stat[ind].get(d, 0) + 1
    matrix = [{"ind": k, "vals": [v.get(d, 0) for d in dd], "total": sum(v.values())}
              for k, v in sorted(ind_stat.items(), key=lambda kv: -sum(kv[1].values()))[:8]]
    return {"days": days_arr, "nodes": nodes, "matrix": matrix, "dates": dd}


def analyze_nameplay(days, dates, lookback=5):
    """字辈挖掘：同一汉字被多只涨停股共享 → 市场共识字辈（华字辈/洋字辈等）。
    活跃 = 今日≥3只；观察 = 今日2只；连燃 = 连续N日≥2只。只统计今日仍出现的字。"""
    dd = dates[-lookback:]
    if not dd:
        return {"active": [], "watch": [], "days": []}
    per_day = []
    for d in dd:
        m = {}
        for r in days[d]["pools"]["zt"]:
            nm = str(r.get("名称") or "")
            lb = int(r.get("连板数") or 0)
            for ch in {c for c in nm if "\u4e00" <= c <= "\u9fff" and c not in NAMEPLAY_STOP}:
                m.setdefault(ch, {})[r.get("代码")] = (nm, lb)
        per_day.append(m)
    today = per_day[-1]
    chars = {}
    for ch in today.keys():
        hist = [len(per_day[i].get(ch, {})) for i in range(len(per_day))]
        streak = 0
        for c in reversed(hist):
            if c >= 2:
                streak += 1
            else:
                break
        t = today[ch]
        chars[ch] = {"ch": ch, "today": len(t), "yesterday": hist[-2] if len(hist) > 1 else 0,
                     "streak": streak, "hist": hist,
                     "max_lb": max(v[1] for v in t.values()),
                     "members": [{"code": c, "name": v[0], "lb": v[1]}
                                 for c, v in sorted(t.items(), key=lambda kv: -kv[1][1])]}
    act = sorted((v for v in chars.values() if v["today"] >= 3),
                 key=lambda x: (-x["today"], -x["max_lb"], -x["streak"], x["ch"]))
    wat = sorted((v for v in chars.values() if v["today"] == 2),
                 key=lambda x: (-x["max_lb"], -x["streak"], x["ch"]))
    return {"active": act, "watch": wat, "days": dd}


def load_themelib_cfg():
    fp = os.path.join(BASE, "themes_custom.json")
    if os.path.exists(fp):
        try:
            return json.load(open(fp, encoding="utf-8")).get("groups", [])
        except Exception:
            pass
    return []


def load_focus_cfg():
    fp = os.path.join(BASE, "focus.json")
    if os.path.exists(fp):
        try:
            return json.load(open(fp, encoding="utf-8")).get("items", [])
        except Exception:
            pass
    return []


def gather_focus(conn, days, dates, name_map):
    """市场聚焦候选：人工 focus.json + 自动（新股C/N前缀 + 资讯并购重组/复牌关键词）。"""
    out, seen = [], set()

    def add(name, code, tag, reason, src, dt):
        if not name or name in seen:
            return
        seen.add(name)
        out.append({"name": str(name), "code": code or "", "tag": tag,
                    "reason": reason, "src": src,
                    "date": dt or (dates[-1] if dates else "")})

    for it in load_focus_cfg():
        add(it.get("name"), it.get("code") or "", it.get("tag") or "聚焦",
            it.get("reason") or "", "人工", it.get("date"))
    # 自动：新股 C/N 前缀（近5日涨停池）
    for d in dates[-5:]:
        for r in days.get(d, {}).get("pools", {}).get("zt", []):
            nm = str(r.get("名称") or "")
            if len(nm) >= 2 and nm[0] in ("C", "N") and "\u4e00" <= nm[1] <= "\u9fff":
                lb = int(r.get("连板数") or 0)
                reason = f"近端次新（{nm[0]}前缀，上市初期无涨跌幅限制），情绪聚焦标的" + (f"，今日{lb}板" if lb else "")
                add(nm, r.get("代码"), "新股", reason, "自动·新股", d)
    # 自动：近7日资讯 并购/重组/复牌 → 匹配股票名
    try:
        import datetime as _dt
        cutoff = (_dt.datetime.now() - _dt.timedelta(days=7)).strftime("%Y-%m-%d")
        rows = conn.execute(
            "SELECT pub_time, title, summary FROM news WHERE pub_time>=? "
            "ORDER BY pub_time DESC LIMIT 400", (cutoff,)).fetchall()
    except Exception:
        rows = []
    kw_tag = [("要约收购", "并购重组"), ("收购", "并购重组"), ("重组", "并购重组"),
              ("借壳", "并购重组"), ("资产注入", "并购重组"), ("复牌", "复牌")]
    names_sorted = sorted(name_map.keys(), key=len, reverse=True)
    for pt, title, summary in rows:
        for kw, tag in kw_tag:
            if kw in str(title):
                for n in names_sorted:
                    if len(n) >= 3 and n in str(title):
                        add(n, name_map.get(n, ""), tag, str(title)[:80], "自动·资讯", str(pt)[:10])
                        break
                break
    return out[:10]


def enrich_focus(cands, quotes, today_zt):
    out = []
    for it in cands:
        code = it.get("code") or ""
        q = quotes.get(code, {})
        pct = q.get("pct")
        zr = today_zt.get(code) if code else None
        lb = int(zr.get("连板数") or 0) if zr else 0
        if pct is None and zr:
            try:
                pct = float(zr.get("涨跌幅"))
            except Exception:
                pct = None
        out.append({"name": it["name"], "code": code, "tag": it["tag"],
                    "reason": it["reason"], "src": it["src"], "date": it["date"],
                    "pct": pct, "lb": lb,
                    "cur_name": q.get("name") or (zr or {}).get("名称") or it["name"]})
    return out


def enrich_themelib(groups, quotes, today_zt):
    out = []
    for g in groups:
        subs, g_zt = [], 0
        for sub in g.get("subs", []):
            members = []
            for code, nm in sub.get("codes", {}).items():
                q = quotes.get(code, {})
                zr = today_zt.get(code)
                lb = int(zr.get("连板数") or 0) if zr else 0
                pct = q.get("pct")
                if pct is None and zr:
                    try:
                        pct = float(zr.get("涨跌幅"))
                    except Exception:
                        pct = None
                members.append({"code": code, "name": nm, "pct": pct, "lb": lb})
            members.sort(key=lambda m: (-(m["pct"] if m["pct"] is not None else -99), -m["lb"]))
            zt_n = sum(1 for m in members if m["lb"])
            g_zt += zt_n
            subs.append({"name": sub["name"], "members": members, "zt": zt_n})
        out.append({"name": g["name"], "type": g.get("type") or "mid", "zt": g_zt, "subs": subs})
    return out


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


def load_unlock(conn, base_date):
    """P8: 未来 30 日解禁日历（相对看板最新交易日，覆盖式快照）"""
    from datetime import datetime as _dt
    base = _dt.strptime(base_date, "%Y%m%d").date()
    rows = conn.execute(
        "SELECT code, name, unlock_date, shares, mv, ratio, share_type FROM unlock_cal "
        "WHERE unlock_date >= ? ORDER BY unlock_date", (base.isoformat(),)).fetchall()
    stocks = [{"代码": c, "名称": n, "日期": u, "mv": round((m or 0) / 10000, 1),
               "ratio": rt, "类型": st}
              for c, n, u, s, m, rt, st in rows if m]
    stocks.sort(key=lambda x: -x["mv"])
    byday = {}
    for c, n, u, s, m, rt, st in rows:
        if not u:
            continue
        d = byday.setdefault(u, {"n": 0, "mv": 0.0})
        d["n"] += 1
        d["mv"] += (m or 0)
    days = sorted(({"date": u, "n": v["n"], "mv": round(v["mv"] / 10000, 1)}
                   for u, v in byday.items()), key=lambda x: x["date"])
    total_mv = round(sum((m or 0) for _, _, _, _, m, _, _ in rows) / 10000, 1)
    return {"total": len(rows), "total_mv": total_mv, "days": days,
            "stocks": stocks[:12]}



def build(dates):
    conn = sqlite3.connect(DB)
    days = {}
    for d in dates:
        pools, breadth = load_day(conn, d)
        # P7: 注入真实涨停原因（同花顺揭秘；缺数个股保留行业归因回退）
        ztr = {str(c): rs for c, rs in conn.execute(
            "SELECT code, reason FROM zt_reasons WHERE date=? AND reason!=''", (d,))}
        for r in pools["zt"]:
            rs = ztr.get(str(r.get("代码") or ""))
            if rs:
                r["涨停原因"] = rs
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
            "seal": analyze_seal_time(pools),
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
    unlock = load_unlock(conn, dates[-1]) if dates else {"total": 0, "total_mv": 0, "days": [], "stocks": []}
    # 聚焦挖掘：字辈 + 市场聚焦 + 题材库（统一一次批量行情）
    nameplay = analyze_nameplay(days, dates)
    focus_cands = gather_focus(conn, days, dates, news_map)
    pool_names = {}
    for d in dates[-10:]:
        for c, n in conn.execute("SELECT code, name FROM pool_daily WHERE date=?", (d,)):
            if n:
                pool_names.setdefault(str(n), str(c))
    for it in focus_cands:
        if not it["code"] and it["name"] in pool_names:
            it["code"] = pool_names[it["name"]]
    themelib_cfg = load_themelib_cfg()
    qcodes = {it["code"] for it in focus_cands if it["code"]}
    for g in themelib_cfg:
        for sub in g.get("subs", []):
            qcodes.update(sub.get("codes", {}).keys())
    quotes = fetch_quotes(qcodes)
    today_zt = {r.get("代码"): r for r in days[dates[-1]]["pools"]["zt"]} if dates else {}
    focus = enrich_focus(focus_cands, quotes, today_zt)
    themelib = enrich_themelib(themelib_cfg, quotes, today_zt)
    timeline = {"day": analyze_day_timeline(days, dates),
                "week": analyze_period_timeline(days, dates, 5),
                "month": analyze_period_timeline(days, dates, 22)}
    conn.close()
    return {"dates": dates, "days": days, "trend": trend, "value": value, "movement": movement,
            "lowpos": lowpos, "screener": screener, "news": news,
            "promotion": promotion, "newsMap": news_map,
            "nameplay": nameplay, "focus": focus, "themelib": themelib,
            "unlock": unlock, "timeline": timeline}
