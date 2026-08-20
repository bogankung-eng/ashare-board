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
            "code": code, "name": names.get(code, code),
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
    elif zbrate >= 40 or dt_n >= 10:
        tag, cls = "局部退潮", "warn"
    elif zt_n >= 80 and zbrate < 25 and max_lb >= 4:
        tag, cls = "情绪加强", "good"
    elif zt_n >= 50 and zbrate < 40:
        tag, cls = "情绪修复", "good"
    else:
        tag, cls = "震荡混沌", "flat"

    return {
        "zt": zt_n, "dt": dt_n, "zb": zb_n, "zbrate": zbrate, "max_lb": max_lb,
        "tag": tag, "tag_cls": cls,
        "top": [{"name": r.get("名称"), "code": r.get("代码"),
                 "lb": int(r.get("连板数") or 0), "ztstat": r.get("涨停统计")} for r in top],
    }


def analyze_stocks(pools):
    """个股延续性评分 + 次日策略（规则引擎 v1）
    四维评分（各 0-3 分）：封板强度 / 封板资金 / 换手质量 / 位置 / 地位
    总分 15：强(≥11) / 中(8-10.5) / 弱(<8)"""
    zt = pools["zt"]
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
        if total >= 11:
            level, level_cls = "强", "lv-strong"
        elif total >= 8:
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
            "name": name, "count": len(arr), "max_lb": max_lb,
            "lb_names": "/".join(str(x) for x in sorted(set(lbs), reverse=True)),
            "total_seal": round(total_seal / 100000000, 2),
            "leader": {"name": leader.get("名称"), "code": leader.get("代码"),
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
            parts.append("高位区: " + "、".join(t["name"] for t in high[:4]) + " —— 注意分歧兑现风险")
        if low:
            parts.append("低位启动: " + "、".join(t["name"] for t in low[:4]) + " —— 观察承接与扩散")
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


def build(dates):
    conn = sqlite3.connect(DB)
    days = {}
    for d in dates:
        pools, breadth = load_day(conn, d)
        analyze_stocks(pools)
        themes, hl_conclusion = analyze_themes(pools, sentiment(pools, breadth))
        ext = load_ext(conn, d)
        days[d] = {
            "breadth": breadth,
            "sent": sentiment(pools, breadth),
            "pools": pools,
            "themes": themes,
            "hl": hl_conclusion,
            "ext": analyze_ext(ext, pools),
        }
    trend = analyze_trend(conn)
    conn.close()
    return {"dates": dates, "days": days, "trend": trend}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股短线看板 · 涨停接力复盘</title>
<style>
  :root{
    --bg:#f7f6f2; --card:#ffffff; --ink:#2b2b2b; --ink2:#6b6b6b; --ink3:#9a9a9a;
    --line:#e6e4dd; --up:#d93025; --upbg:#fdecec; --down:#188038; --downbg:#e9f5ec;
    --blue:#185fa5; --bluebg:#e8f1fa; --amber:#b45309; --amberbg:#fdf3e0;
    --purple:#534ab7; --purplebg:#efedfc;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:var(--bg); color:var(--ink); font-family:"PingFang SC","Microsoft YaHei",-apple-system,sans-serif; line-height:1.6; font-size:14px;}
  .wrap{max-width:1180px; margin:0 auto; padding:20px 16px 60px;}
  .topbar{display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:14px;}
  h1{font-size:20px; font-weight:600;}
  .sub{color:var(--ink2); font-size:12.5px;}
  .datebar{display:flex; gap:6px; flex-wrap:wrap;}
  .datebtn{border:1px solid var(--line); background:#fbfaf7; border-radius:8px; padding:5px 14px; font-size:13px; cursor:pointer; color:var(--ink2);}
  .datebtn.active{background:var(--blue); color:#fff; border-color:var(--blue); font-weight:600;}
  .card{background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin-bottom:14px;}
  .sent-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(105px,1fr)); gap:10px;}
  .sent-item{border:1px solid var(--line); border-radius:10px; padding:10px 12px; background:#fbfaf7; text-align:center;}
  .sent-item .label{font-size:12px; color:var(--ink2);}
  .sent-item .value{font-size:20px; font-weight:600; margin-top:2px;}
  .sent-item .subv{font-size:11.5px; color:var(--ink3); margin-top:2px;}
  .tag-big{font-size:15px; font-weight:600; padding:2px 12px; border-radius:8px; display:inline-block;}
  .tag-good{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .tag-danger{background:#4a0f0f; color:#ffd9d9; border:1px solid #7a1f1f;}
  .tag-warn{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .tag-flat{background:#f1efe9; color:var(--ink2); border:1px solid var(--line);}
  .filters{display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end;}
  .f-item{display:flex; flex-direction:column; gap:4px;}
  .f-item label{font-size:11.5px; color:var(--ink2);}
  .f-item select,.f-item input{border:1px solid var(--line); border-radius:8px; padding:6px 10px; font-size:13px; background:#fff; color:var(--ink);}
  .f-item input{width:72px;}
  .ind-tags{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;}
  .ind-tag{border:1px solid var(--line); background:#fbfaf7; border-radius:16px; padding:3px 12px; font-size:12px; cursor:pointer; color:var(--ink2); user-select:none;}
  .ind-tag.on{background:var(--bluebg); color:var(--blue); border-color:#9cc4e8; font-weight:600;}
  .btn{border:1px solid var(--line); background:#fbfaf7; border-radius:8px; padding:6px 14px; font-size:13px; cursor:pointer; color:var(--ink2);}
  .btn:hover{border-color:var(--ink3);}
  .grp{margin-bottom:16px;}
  .grp-head{display:flex; align-items:center; gap:10px; margin-bottom:8px; padding:8px 12px; border-radius:10px; font-weight:600; font-size:14px;}
  .grp-head .cnt{font-size:12px; font-weight:400; color:var(--ink2);}
  .g-lb4{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0;}
  .g-lb3{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .g-lb2{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .g-lb1{background:#f1efe9; color:var(--ink2); border:1px solid var(--line);}
  table{width:100%; border-collapse:collapse; font-size:12.5px;}
  th{background:#f1efe9; text-align:left; padding:7px 8px; border:1px solid var(--line); font-weight:600; white-space:nowrap;}
  td{padding:6px 8px; border:1px solid var(--line); white-space:nowrap;}
  tr:nth-child(even) td{background:#fbfaf7;}
  .up{color:var(--up); font-weight:600;}
  .down{color:var(--down); font-weight:600;}
  .num{font-family:Consolas,"SF Mono",monospace;}
  .code{color:var(--ink2); font-family:Consolas,monospace;}
  .pill{display:inline-block; font-size:11px; border-radius:5px; padding:0 6px;}
  .pill-zt{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .pill-zb{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .pill-lv{border-radius:6px; padding:1px 8px; font-size:11.5px; font-weight:600;}
  .lv-strong{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .lv-mid{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .lv-weak{background:#f1efe9; color:var(--ink2); border:1px solid var(--line);}
  .theme-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px;}
  .theme-card{border:1px solid var(--line); border-radius:10px; padding:11px 14px; background:#fbfaf7;}
  .theme-card .tname{font-weight:600; font-size:14px;}
  .theme-card .tmeta{font-size:12px; color:var(--ink2); margin-top:4px; line-height:1.8;}
  .stage-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600;}
  .st-good{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2;}
  .st-warn{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .st-danger{background:#4a0f0f; color:#ffd9d9; border:1px solid #7a1f1f;}
  .st-flat{background:#f1efe9; color:var(--ink2); border:1px solid var(--line);}
  .hl-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-left:6px;}
  .hl-good{background:var(--bluebg); color:var(--blue); border:1px solid #9cc4e8;}
  .hl-warn{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .hl-card{background:var(--bluebg); border:1px solid #c9ddef; border-radius:10px; padding:12px 16px; margin-top:12px; font-size:13px;}
  .hl-card b{color:var(--blue);}
  .empty{color:var(--ink3); text-align:center; padding:30px 0;}
  .foot{margin-top:20px; font-size:11.5px; color:var(--ink3); text-align:center;}
  .disclaimer{background:#f5f5f2; border:1px solid var(--line); border-radius:10px; padding:10px 14px; font-size:12px; color:var(--ink2); margin-top:12px;}
  .lv-tip{cursor:help; border-bottom:1px dashed var(--ink3);}
  .sub-grid{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
  @media (max-width:900px){.sub-grid{grid-template-columns:1fr;}}
  .sub-box{border:1px solid var(--line); border-radius:10px; padding:12px 14px; background:#fbfaf7;}
  .sub-box h4{font-size:13.5px; margin-bottom:8px; color:var(--ink);}
  .lhb-row{display:flex; align-items:center; gap:8px; padding:5px 0; border-bottom:1px dashed var(--line); font-size:12.5px;}
  .lhb-row:last-child{border-bottom:none;}
  .lhb-row .nm{flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  .lhb-row .amt{font-family:Consolas,monospace; font-weight:600;}
  .money-in{color:var(--up);}
  .money-out{color:var(--down);}
  .focus-tag{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0; border-radius:5px; font-size:10.5px; padding:0 5px;}
  .prev-stats{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px;}
  .prev-stat{border:1px solid var(--line); border-radius:10px; padding:8px 16px; background:#fbfaf7; text-align:center; min-width:90px;}
  .prev-stat .v{font-size:18px; font-weight:600;}
  .prev-stat .l{font-size:11px; color:var(--ink2);}
  .two-col{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
  @media (max-width:900px){.two-col{grid-template-columns:1fr;}}
  .mini-list{border:1px solid var(--line); border-radius:10px; padding:8px 10px; background:#fbfaf7; font-size:12px;}
  .mini-list .row{padding:3px 0; border-bottom:1px dashed var(--line); display:flex; gap:6px; align-items:center;}
  .mini-list .row:last-child{border-bottom:none;}
  .mini-list .c{color:var(--ink3); font-family:Consolas,monospace; font-size:11px;}
  .tabs-wrap input{display:none;}
  .tabs{display:flex; gap:8px; margin:0 0 16px;}
  .tabs label{display:inline-block; padding:9px 22px; border:1px solid var(--line); border-radius:24px; cursor:pointer; font-size:14px; background:#fbfaf7; color:var(--ink2); user-select:none; font-weight:600;}
  #tab-short:checked ~ .tabs label[for="tab-short"],
  #tab-trend:checked ~ .tabs label[for="tab-trend"]{background:var(--blue); color:#fff; border-color:var(--blue);}
  .panel{display:none;}
  #tab-short:checked ~ .panel-short,
  #tab-trend:checked ~ .panel-trend{display:block;}
  .idx-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:10px;}
  .idx-card{border:1px solid var(--line); border-radius:10px; padding:10px 14px; background:#fbfaf7;}
  .idx-card .iname{font-weight:600; font-size:13.5px;}
  .idx-card .ival{font-size:16px; font-weight:600; margin:2px 0;}
  .idx-card .imeta{font-size:11.5px; color:var(--ink2); line-height:1.7;}
  .st-bull{background:var(--upbg); color:var(--up); border:1px solid #f3c4c2; border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .st-bear{background:var(--downbg); color:var(--down); border:1px solid #c2e3cc; border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .st-mix{background:#f1efe9; color:var(--ink2); border:1px solid var(--line); border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .sig-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-right:4px;}
  .sig-bk{background:var(--purplebg); color:var(--purple); border:1px solid #d8d4f0;}
  .sig-pb{background:var(--amberbg); color:var(--amber); border:1px solid #f0d9ac;}
  .sig-hi{background:var(--bluebg); color:var(--blue); border:1px solid #9cc4e8;}
</style>
</head>
<body>
<div class="wrap">
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
    <div class="tabs">
      <label for="tab-short">短线复盘</label>
      <label for="tab-trend">中长线趋势</label>
    </div>

  <div class="panel panel-short">
  <div class="card">
    <div id="sentiment"></div>
  </div>

  <div class="card">
    <div id="themes-card"></div>
  </div>

  <div class="card">
    <div id="ext-card"></div>
  </div>

  <div class="card">
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
        <label>首次封板时间</label>
        <select id="f-seal">
          <option value="all">全部</option>
          <option value="early">早盘 ≤10:00</option>
          <option value="mid">盘中 10:00-14:30</option>
          <option value="late">尾盘 ≥14:30</option>
        </select>
      </div>
      <div class="f-item">
        <label>炸板次数</label>
        <select id="f-zb">
          <option value="all">全部</option>
          <option value="0">0 次（干净板）</option>
          <option value="1">≥1 次</option>
        </select>
      </div>
      <div class="f-item">
        <label>筛选</label>
        <button class="btn" id="f-reset" type="button">重置</button>
      </div>
    </div>
    <div class="ind-tags" id="ind-tags"></div>
  </div>

  <div class="card">
    <div id="pool"></div>
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
  </div>

  <div class="disclaimer"><b>免责声明：</b>本看板数据来自公开行情接口（东方财富/乐咕乐股），仅供个人复盘研究参考，不构成投资建议。市场有风险，投资需谨慎。涨停原因、题材归类等字段将在后续版本完善。</div>
  <div class="foot">A股短线看板 · 由 _gen_board.py 生成 · 数据仅供复盘参考</div>
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
      ["连板高度", s.max_lb + "板", s.top.length ? (s.top[0].name + " " + s.top[0].ztstat) : "无连板"],
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
        '<div><span class="tname">' + esc(t.name) + '</span>' +
        '<span class="stage-tag st-' + t.stage_cls + '">' + t.stage + '</span>' +
        (t.hl ? '<span class="hl-tag hl-' + t.hl_cls + '">' + t.hl + '</span>' : '') + '</div>' +
        '<div class="tmeta">涨停 <b>' + t.count + '</b> 家 · 高度 ' + t.max_lb + '板 (' + t.lb_names + ')<br>' +
        '封板资金 ' + t.total_seal + '亿 · 龙头 <b>' + esc(t.leader.name) + '</b> (' + t.leader.lb + '板)</div>' +
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
        html += '<tr>' +
          '<td class="code">' + esc(r["代码"]) + '</td>' +
          '<td><b>' + esc(r["名称"]) + '</b></td>' +
          '<td class="up num">' + Number(r["涨跌幅"]).toFixed(2) + '%</td>' +
          '<td class="num">' + Number(r["最新价"]).toFixed(2) + '</td>' +
          '<td>' + ztstat + '</td>' +
          '<td>' + esc(r["_reason"] || r["所属行业"] || "-") + '</td>' +
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
      html += '<div class="sub-grid" style="margin-top:12px;">';
      if (hasLhb) {
        html += '<div class="sub-box"><h4>龙虎榜 · 净买额 TOP（' + (ext.lhb_zt.length ? "★涨停+上榜焦点" : "当日上榜") + '）</h4>';
        var list = ext.lhb_zt.length ? ext.lhb_zt : ext.lhb_top_buy;
        list.slice(0, 8).forEach(function (r) {
          var net = Number(r["龙虎榜净买额"] || 0);
          html += '<div class="lhb-row"><span class="nm"><b>' + esc(r["名称"]) + '</b> <span class="c">' + esc(r["代码"]) + '</span>' +
            (ext.lhb_zt.indexOf(r) >= 0 ? ' <span class="focus-tag">涨停</span>' : '') + '</span>' +
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
      html += '</div>';
    }
    box.innerHTML = html;
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
        '<td><b>' + esc(r.name) + '</b></td>' +
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

  function renderAll() {
    renderSentiment();
    renderThemes();
    renderExt();
    renderTrend();
    buildIndTags();
    renderPool();
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
