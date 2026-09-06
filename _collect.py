#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股行情看板 · P0 数据采集器
采集：涨停池 / 跌停池 / 炸板池 / 市场广度（涨跌家数）
存储：SQLite 历史累积（data/board.db）+ 当日 JSON 快照（data/snapshot_YYYYMMDD.json）
用法：
    python _collect.py                  # 采集今天（非交易日自动跳过）
    python _collect.py --date=20260818  # 采集指定日期
    python _collect.py --date=20260818 --force  # 强制重采（覆盖已有）
"""
import argparse
import hashlib
import json
import os
import socket
import sqlite3
import threading
import time
from datetime import date, datetime

import akshare as ak

# 防第三方行情接口无响应挂起（requests 默认无限等待 → 脚本卡死）
# 2026-08-26 修复：新浪/东财接口偶发"连接成功但无响应"，此前曾卡死 18+ 分钟
socket.setdefaulttimeout(20)

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "board.db")
SNAP_DIR = os.path.join(BASE, "data")

POOLS = {
    "zt": ("stock_zt_pool_em", "涨停池"),
    "dt": ("stock_zt_pool_dtgc_em", "跌停池"),
    "zb": ("stock_zt_pool_zbgc_em", "炸板池"),
}

# P4 中长线趋势：主要指数（新浪源）
IDX = {
    "sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
    "sh000688": "科创50", "sh000300": "沪深300",
}


def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS pool_daily("
        "date TEXT, pool_type TEXT, code TEXT, name TEXT, data_json TEXT, "
        "collected_at TEXT, PRIMARY KEY(date, pool_type, code))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS breadth("
        "date TEXT PRIMARY KEY, up INT, down INT, flat INT, "
        "limit_up INT, limit_down INT, total INT, activity TEXT, data_json TEXT, collected_at TEXT)"
    )
    try:  # 兼容旧库：补齐新增列
        for col in ("activity TEXT", "data_json TEXT"):
            conn.execute(f"ALTER TABLE breadth ADD COLUMN {col}")
    except sqlite3.OperationalError:
        pass
    conn.execute("CREATE TABLE IF NOT EXISTS trade_cal(date TEXT PRIMARY KEY)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS collect_log("
        "date TEXT PRIMARY KEY, status TEXT, collected_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS lhb("
        "date TEXT, code TEXT, reason TEXT, name TEXT, data_json TEXT, "
        "collected_at TEXT, PRIMARY KEY(date, code, reason))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS fund_flow("
        "date TEXT, sector_type TEXT, data_json TEXT, "
        "collected_at TEXT, PRIMARY KEY(date, sector_type))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS prev_zt("
        "date TEXT, code TEXT, name TEXT, data_json TEXT, "
        "collected_at TEXT, PRIMARY KEY(date, code))"
    )
    # P4 中长线趋势：指数日线 + 候选池个股 K 线
    conn.execute(
        "CREATE TABLE IF NOT EXISTS idx_daily("
        "code TEXT, name TEXT, date TEXT, close REAL, volume REAL, PRIMARY KEY(code, date))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kline("
        "code TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
        "volume REAL, amount REAL, pct REAL, PRIMARY KEY(code, date))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS trend_cand("
        "date TEXT, code TEXT, name TEXT, PRIMARY KEY(date, code))"
    )
    # P5 长线价值：估值历史 + 财务多期
    conn.execute(
        "CREATE TABLE IF NOT EXISTS value_hist("
        "code TEXT, date TEXT, close REAL, pe_ttm REAL, pe_static REAL, pb REAL, "
        "total_mv REAL, PRIMARY KEY(code, date))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS fin_hist("
        "code TEXT, date TEXT, roe REAL, profit_margin REAL, debt_ratio REAL, "
        "cf_roa REAL, rev_growth REAL, profit_growth REAL, PRIMARY KEY(code, date))"
    )
    # P6-A 龙虎榜席位明细
    conn.execute(
        "CREATE TABLE IF NOT EXISTS seat_daily("
        "date TEXT, code TEXT, seat TEXT, buy_amt REAL, sell_amt REAL, net REAL, "
        "reason TEXT, PRIMARY KEY(date, code, seat, reason))"
    )
    # 公告资讯（新浪快讯/财经早餐 + 人工补充）
    conn.execute(
        "CREATE TABLE IF NOT EXISTS news("
        "id TEXT PRIMARY KEY, date TEXT, pub_time TEXT, title TEXT, summary TEXT, "
        "link TEXT, source TEXT, category TEXT DEFAULT '其他', "
        "sentiment TEXT DEFAULT '中性', reason TEXT DEFAULT '')"
    )
    return conn


NEWS_RULES = {
    "业绩": ["业绩预告", "预增", "预减", "净利", "营收", "年报", "中报", "季报", "扭亏", "业绩"],
    "增减持": ["增持", "减持", "举牌", "要约收购", "股份转让"],
    "回购": ["回购", "注销股份", "回购注销"],
    "质押": ["质押", "解押", "冻结", "司法"],
    "问询": ["问询函", "关注函", "监管函", "立案", "处罚", "警示函", "监管措施"],
    "政策": ["政策", "央行", "证监会", "国务院", "发改委", "财政部", "降准", "降息",
             "利率", "新规", "指导意见", "部署", "会议"],
    "宏观": ["GDP", "CPI", "PPI", "PMI", "社融", "出口", "失业率", "工业增加值", "经济数据"],
    "观点": ["券商", "机构", "首席", "分析师", "研报", "策略", "预计", "认为", "看好"],
}
NEWS_POS = ["预增", "业绩增长", "扭亏", "增持", "回购", "中标", "获批", "分红", "超预期",
            "突破", "涨价", "降准", "降息", "利好", "看好", "扩张", "创新高", "增长", "提升", "新高"]
NEWS_NEG = ["减持", "预减", "亏损", "下滑", "质押", "问询函", "关注函", "监管函", "立案",
            "处罚", "警示", "退市", "冻结", "不及预期", "下调", "收缩", "风险", "违约", "诉讼", "商誉减值"]
# 相关度过滤：只保留与 A股市场 / 政策 / 宏观 / 公司基本面 相关的资讯
NEWS_REL = ["A股", "沪指", "深证", "创业板", "科创板", "北交所", "港股", "涨停", "跌停",
            "证监会", "交易所", "IPO", "上市", "退市", "基金", "券商", "机构", "北向", "主力",
            "央行", "财政部", "发改委", "工信部", "国资委", "政策", "新规", "监管",
            "降准", "降息", "GDP", "CPI", "PPI", "PMI", "社融", "经济数据",
            "回购", "减持", "增持", "质押", "问询", "业绩", "营收", "净利", "预增", "预减",
            "分红", "中标", "订单", "并购", "重组", "定增", "股东", "股价", "上市公司"]


def classify_news(text):
    """返回 (分类, 情感, 依据关键词串)"""
    cat = "其他"
    for k, kws in NEWS_RULES.items():
        if any(w in text for w in kws):
            cat = k
            break
    pos_hits = [w for w in NEWS_POS if w in text]
    neg_hits = [w for w in NEWS_NEG if w in text]
    if len(neg_hits) > len(pos_hits):
        sent, hits = "利空", neg_hits
    elif pos_hits:
        sent, hits = "利好", pos_hits
    else:
        sent, hits = "中性", []
    return cat, sent, "、".join(hits[:4])


def fetch_news(conn, date_str, now):
    """公告资讯：新浪全球快讯 + 财经早餐（自动）+ news_manual.json（人工补充）"""
    rows = []

    def _add(title, summary, pub_time, link, source):
        text = f"{title} {summary}"
        # 相关度过滤：自动源只保留 A股/政策/宏观/基本面相关（人工源不过滤）
        if source != "人工" and not any(w in text for w in NEWS_REL):
            return
        cat, sent, reason = classify_news(text)
        nid = hashlib.md5(f"{title}|{pub_time}".encode("utf-8")).hexdigest()[:16]
        rows.append((nid, date_str, pub_time, str(title)[:120], str(summary)[:400],
                     str(link)[:300], source, cat, sent, reason))

    for fn_name, src in [("stock_info_global_em", "新浪快讯"), ("stock_info_cjzc_em", "财经早餐")]:
        fn = getattr(ak, fn_name, None)
        if not fn:
            continue
        df = call_with_retry(fn, retries=2)
        if df is None or df.empty:
            continue
        for r in df.to_dict(orient="records"):
            pt = str(r.get("发布时间", "")) or ""
            title = str(r.get("标题", "")).strip()
            if not title:
                continue
            if pt[:10].replace("-", "") not in (date_str, "", None) and pt[:10].replace("-", "") < date_str:
                # 只保留当日及之后的（新浪返回最新 N 条）
                if pt[:10].replace("-", "") < date_str:
                    continue
            _add(title, str(r.get("摘要", ""))[:400], pt, r.get("链接", ""), src)
        time.sleep(0.3)

    # 人工补充（结构化公告：问询函/减持/质押/业绩预告等，接口不可用时手动维护）
    mf = os.path.join(BASE, "news_manual.json")
    if os.path.exists(mf):
        try:
            for ev in json.load(open(mf, encoding="utf-8")).get("events", []):
                _add(ev.get("title", ""), ev.get("summary", ""),
                     ev.get("pub_time", date_str + " 18:00"),
                     ev.get("link", ""), ev.get("source", "人工"))
        except Exception:
            pass

    if not rows:
        print("[跳过] 资讯为空")
        return
    conn.executemany(
        "INSERT OR REPLACE INTO news(id,date,pub_time,title,summary,link,source,category,"
        "sentiment,reason) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    print(f"[OK] 公告资讯 {len(rows)} 条", flush=True)


def load_trade_cal(conn):
    """交易日历：首次从新浪拉全量，之后读本地"""
    if conn.execute("SELECT COUNT(*) FROM trade_cal").fetchone()[0] == 0:
        df = ak.tool_trade_date_hist_sina()
        rows = [(str(d).replace("-", "")[:8],) for d in df["trade_date"]]
        conn.executemany("INSERT OR IGNORE INTO trade_cal(date) VALUES (?)", rows)
        conn.commit()
        print(f"[日历] 已初始化 {len(rows)} 个交易日")
    return {r[0] for r in conn.execute("SELECT date FROM trade_cal")}


def _call_timeout(fn, timeout, **kw):
    """线程级看门狗：任何调用超过 timeout 秒即放弃（防接口无响应挂死）。
    注：socket 全局超时对部分接口不生效（akshare 显式传 timeout 参数会覆盖），
    故改用线程 join 兜底。挂起线程为 daemon，进程退出时自动清理。"""
    box = {}

    def worker():
        try:
            box["df"] = fn(**kw)
            box["ok"] = True
        except Exception as e:  # noqa: BLE001
            box["err"] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"{getattr(fn, '__name__', fn)} 调用超过 {timeout}s 无响应，已放弃")
    if "err" in box:
        raise box["err"]
    return box.get("df")


def call_with_retry(fn, retries=3, timeout=20, empty_ok=False, **kw):
    """指数退避重试；akshare 爬虫类接口偶发失败/风控，间隔拉长降低触发概率。
    2026-08-26 加固：线程级看门狗，任何挂起调用到 timeout 秒即放弃重试，防止脚本无限卡死。
    empty_ok=True：空表视为合法（业务上可能无数据，如无跌停/无炸板日），不重试直接返回。"""
    waits = [5, 15, 30]
    for i in range(retries):
        try:
            df = _call_timeout(fn, timeout, **kw)
            if df is not None and len(df) > 0:
                return df
            if empty_ok:
                return df
            print(f"  [重试{i+1}] 返回空数据")
        except Exception as e:
            print(f"  [重试{i+1}] {type(e).__name__}: {str(e)[:120]}")
        time.sleep(waits[i] if i < len(waits) else 60)
    return None


def fetch_pool(kind, date_str):
    """采集单类股票池，返回 [{列名: 值}, ...]
    跌停/炸板池空表 = 当日无此池个股（业务合法），不重试；涨停池空表视为异常仍重试。"""
    fn_name = POOLS[kind][0]
    df = call_with_retry(getattr(ak, fn_name), date=date_str, empty_ok=kind in ("dt", "zb"))
    if df is None:
        return None, None
    rows = df.to_dict(orient="records")
    # 标准化：code/name 列统一命名
    norm = []
    for r in rows:
        item = {str(k): _jsonable(v) for k, v in r.items()}
        code = str(item.get("代码", "")).strip()
        name = str(item.get("名称", "")).strip()
        norm.append((code, name, item))
    return norm, len(df)


def _jsonable(v):
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    if hasattr(v, "item"):  # numpy 标量
        try:
            return v.item()
        except Exception:
            return str(v)
    return str(v)


def calc_breadth(target_date=None):
    """市场广度三级降级：
    1) 乐咕乐股 stock_market_activity_legu（轻量稳定，含真实涨停/活跃度；仅支持最新交易日）
    2) 东财全市场快照（被限流时失败）
    3) 新浪全市场快照（反爬时失败）"""
    # 一级：乐咕乐股（仅最新数据，校验统计日期防错配）
    try:
        df = ak.stock_market_activity_legu()
        if df is not None and len(df) > 0:
            kv = dict(zip(df["item"], df["value"]))
            stat_date = str(kv.get("统计日期", ""))[:10].replace("-", "")
            if target_date and stat_date != target_date:
                print(f"  [广度] 乐咕统计日 {stat_date} ≠ 目标 {target_date}（接口仅最新），跳过")
                return None
            def _g(k):
                v = kv.get(k)
                return int(v) if v is not None and v == v else 0
            b = {
                "up": _g("上涨"), "down": _g("下跌"), "flat": _g("平盘"),
                "limit_up": _g("涨停"), "limit_down": _g("跌停"),
                "real_zt": _g("真实涨停"), "real_dt": _g("真实跌停"),
                "total": _g("上涨") + _g("下跌") + _g("平盘") + _g("停牌"),
                "activity": str(kv.get("活跃度", "")),
                "source": "legu", "raw": {str(k): v for k, v in kv.items()},
            }
            print(f"  [广度] 乐咕乐股: 涨{b['up']} 跌{b['down']} 平{b['flat']} 真涨停{b['real_zt']}")
            return b
    except Exception as e:
        print(f"  [广度] 乐咕乐股失败: {str(e)[:80]}")

    # 二级/三级：全市场快照（东财优先，新浪兜底）
    for src in ("em", "sina"):
        fn = ak.stock_zh_a_spot_em if src == "em" else ak.stock_zh_a_spot
        df = call_with_retry(fn, retries=2)
        if df is not None:
            pct = df["涨跌幅"].dropna()
            up = int((pct > 0).sum())
            down = int((pct < 0).sum())
            flat = int((pct == 0).sum())
            print(f"  [广度] 全市场快照 source={src} 总数={len(df)}")
            return {"up": up, "down": down, "flat": flat, "total": int(len(df)), "source": src}
    return None


def fetch_lhb(conn, date_str, now):
    """龙虎榜明细（东财源，晚间披露）"""
    df = call_with_retry(ak.stock_lhb_detail_em, start_date=date_str, end_date=date_str, retries=2)
    if df is None:
        print("[跳过] 龙虎榜获取失败（晚间可能未披露完，21:30 后再试）")
        return
    rows = []
    for r in df.to_dict(orient="records"):
        item = {str(k): _jsonable(v) for k, v in r.items()}
        rows.append((date_str, str(item.get("代码", "")), str(item.get("解读", "")),
                     str(item.get("名称", "")), json.dumps(item, ensure_ascii=False), now))
    conn.executemany("INSERT OR REPLACE INTO lhb(date, code, reason, name, data_json, collected_at)"
                     " VALUES (?,?,?,?,?,?)", rows)
    print(f"[OK] 龙虎榜 {len(rows)} 条")


def fetch_fund_flow(conn, date_str, now):
    """板块资金流（同花顺源，仅即时=最新交易日；历史日跳过防日期错配）"""
    today = date.today().strftime("%Y%m%d")
    if date_str != today:
        print("[跳过] 板块资金流仅支持最新交易日（同花顺即时口径），历史日不采")
        return
    df = call_with_retry(ak.stock_fund_flow_industry, symbol="即时", retries=2)
    if df is None:
        print("[跳过] 板块资金流获取失败")
        return
    rows = [r for r in df.to_dict(orient="records")]
    conn.execute("INSERT OR REPLACE INTO fund_flow(date, sector_type, data_json, collected_at)"
                 " VALUES (?,?,?,?)",
                 (date_str, "industry", json.dumps([{str(k): _jsonable(v) for k, v in r.items()} for r in rows], ensure_ascii=False), now))
    print(f"[OK] 板块资金流（行业）{len(rows)} 个行业")


def fetch_prev_zt(conn, date_str, now):
    """昨日涨停跟踪：date 当日对昨日涨停股的表现统计"""
    df = call_with_retry(ak.stock_zt_pool_previous_em, date=date_str, retries=2)
    if df is None:
        print("[跳过] 昨日涨停跟踪获取失败")
        return
    rows = []
    for r in df.to_dict(orient="records"):
        item = {str(k): _jsonable(v) for k, v in r.items()}
        rows.append((date_str, str(item.get("代码", "")), str(item.get("名称", "")),
                     json.dumps(item, ensure_ascii=False), now))
    conn.executemany("INSERT OR REPLACE INTO prev_zt(date, code, name, data_json, collected_at)"
                     " VALUES (?,?,?,?,?)", rows)
    print(f"[OK] 昨日涨停跟踪 {len(rows)} 只")


def fetch_idx_daily(conn, now):
    """P4: 5 大指数日线（新浪源，增量更新近 300 日）"""
    for code, name in IDX.items():
        last = conn.execute("SELECT MAX(date) FROM idx_daily WHERE code=?", (code,)).fetchone()[0]
        df = call_with_retry(ak.stock_zh_index_daily, symbol=code, retries=2)
        if df is None:
            print(f"  [指数] {name} 获取失败")
            continue
        df = df.tail(300)
        rows = []
        for _, r in df.iterrows():
            d = str(r["date"])[:10]
            if last and d <= last:
                continue
            rows.append((code, name, d, float(r["close"]), float(r["volume"])))
        if rows:
            conn.executemany("INSERT OR REPLACE INTO idx_daily(code,name,date,close,volume)"
                             " VALUES (?,?,?,?,?)", rows)
    conn.commit()
    print(f"[OK] 指数日线更新（{len(IDX)} 个指数）")


def symbol_pre(sym):
    """6/9 开头沪市，0/3/2 开头深市，其余北交所"""
    s = str(sym).strip()
    if s.startswith(("6", "9")):
        return "sh" + s
    if s.startswith(("0", "3", "2")):
        return "sz" + s
    return "bj" + s


def fetch_kline(conn, date_str, now):
    """P4: 候选池 K 线（强势股池 + 涨停池连板≥2），新浪源，增量更新"""
    codes = {}
    df = call_with_retry(ak.stock_zt_pool_strong_em, date=date_str, retries=2)
    if df is not None:
        for r in df.to_dict(orient="records"):
            c = str(r.get("代码", "")).strip()
            if c:
                codes.setdefault(c, str(r.get("名称", "")).strip())
    # 涨停池补充：只取连板≥2 的活跃票
    for d in [r[0] for r in conn.execute(
            "SELECT DISTINCT date FROM collect_log WHERE status='ok' AND date<=? "
            "ORDER BY date DESC LIMIT 3", (date_str,))]:
        for c, n, j in conn.execute(
                "SELECT code, name, json_extract(data_json,'$.连板数') FROM pool_daily "
                "WHERE date=? AND pool_type='zt'", (d,)):
            if (j or 0) >= 2:
                codes.setdefault(c, n)
    # 龙虎榜股补充（席位胜率画像需要其 K 线）
    for c, n in conn.execute(
            "SELECT DISTINCT lhb.code, lhb.name FROM lhb WHERE date=?", (date_str,)):
        codes.setdefault(c, n)

    if not codes:
        print("[跳过] 候选池为空")
        return
    # 候选名称存档（供看板展示，独立于 K 线增量）
    conn.executemany("INSERT OR REPLACE INTO trend_cand(date,code,name) VALUES (?,?,?)",
                     [(date_str, c, n) for c, n in codes.items()])
    conn.commit()
    todo = []
    for c in codes:
        last = conn.execute("SELECT MAX(date) FROM kline WHERE code=?", (c,)).fetchone()[0]
        if last and last.replace("-", "") >= date_str:
            continue
        todo.append(c)
    print(f"[K线] 候选 {len(codes)} 只，待更新 {len(todo)} 只", flush=True)
    n_ok = 0
    for i, c in enumerate(todo):
        df = call_with_retry(ak.stock_zh_a_daily, symbol=symbol_pre(c),
                             adjust="qfq", retries=2)
        if df is None or len(df) == 0:
            continue
        last = conn.execute("SELECT MAX(date) FROM kline WHERE code=?", (c,)).fetchone()[0]
        rows = []
        for _, r in df.tail(300).iterrows():
            d = str(r["date"])[:10]
            if last and d <= last:
                continue
            rows.append((c, d, float(r["open"]), float(r["high"]), float(r["low"]),
                         float(r["close"]), float(r["volume"]),
                         float(r.get("amount") or 0), None))
        if rows:
            conn.executemany("INSERT OR REPLACE INTO kline(code,date,open,high,low,close,volume,amount,pct)"
                             " VALUES (?,?,?,?,?,?,?,?,?)", rows)
            n_ok += 1
        if (i + 1) % 30 == 0:
            conn.commit()
            print(f"  [K线] 进度 {i+1}/{len(todo)}", flush=True)
        time.sleep(0.1)
    conn.commit()
    print(f"[OK] K线更新 {n_ok} 只（新浪源）", flush=True)


def fetch_value(conn, date_str, now):
    """P5: 价值候选池（价值股 + 蓝筹股双池）——估值历史（stock_value_em，增量）+ 财务多期（新浪，覆盖）"""
    watch = {}
    for fn in ("value_watchlist.json", "bluechip_watchlist.json", "growth_watchlist.json"):
        wl = os.path.join(BASE, fn)
        if os.path.exists(wl):
            try:
                watch.update(json.load(open(wl, encoding="utf-8")))
            except Exception:
                pass
    if not watch:
        print("[跳过] 价值/蓝筹候选池为空")
        return

    # 1) 估值历史（增量：只补最新日期之后）
    v_new = 0
    for code, name in watch.items():
        last = conn.execute("SELECT MAX(date) FROM value_hist WHERE code=?", (code,)).fetchone()[0]
        df = call_with_retry(ak.stock_value_em, symbol=code, retries=2)
        if df is None or len(df) == 0:
            print(f"  [估值] {name} 获取失败")
            continue
        rows = []
        for _, r in df.iterrows():
            d = str(r["数据日期"])[:10]
            if last and d <= last:
                continue
            rows.append((code, d, _jsonable(r["当日收盘价"]), _jsonable(r["PE(TTM)"]),
                         _jsonable(r["PE(静)"]), _jsonable(r["市净率"]),
                         _jsonable(r["总市值"])))
        if rows:
            conn.executemany("INSERT OR REPLACE INTO value_hist(code,date,close,pe_ttm,pe_static,pb,total_mv)"
                             " VALUES (?,?,?,?,?,?,?)", rows)
            v_new += len(rows)
    conn.commit()
    print(f"[OK] 估值历史更新 {v_new} 行（{len(watch)} 只）", flush=True)

    # 2) 财务多期（覆盖式，季报级；失败不中断主流程）
    f_ok = 0
    for code, name in watch.items():
        try:
            df = call_with_retry(ak.stock_financial_analysis_indicator,
                                 symbol=code, start_year=str(int(date_str[:4]) - 4), retries=2)
            if df is None or len(df) == 0:
                continue
        except Exception as e:
            print(f"  [财务] {name} 失败: {str(e)[:60]}")
            continue
        rows = []
        for _, r in df.iterrows():
            def _g(col):
                v = r.get(col)
                if v is None:
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
            rows.append((code, str(r["日期"])[:10], _g("净资产收益率(%)"),
                         _g("销售净利率(%)"), _g("资产负债率(%)"),
                         _g("资产的经营现金流量回报率(%)"),
                         _g("主营业务收入增长率(%)"), _g("净利润增长率(%)")))
        if rows:
            conn.executemany("INSERT OR REPLACE INTO fin_hist(code,date,roe,profit_margin,debt_ratio,cf_roa,rev_growth,profit_growth)"
                             " VALUES (?,?,?,?,?,?,?,?)", rows)
            f_ok += 1
        time.sleep(0.1)
    conn.commit()
    print(f"[OK] 财务指标更新 {f_ok} 只", flush=True)


def fetch_seats(conn, date_str, now):
    """P6-A: 龙虎榜席位明细（对当日上榜股逐只拉买卖前五席位）"""
    codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM lhb WHERE date=?", (date_str,))]
    if not codes:
        print("[跳过] 当日无龙虎榜数据")
        return
    n_ok = 0
    for i, code in enumerate(codes):
        df = call_with_retry(ak.stock_lhb_stock_detail_em, symbol=code, date=date_str, retries=1)
        if df is None or len(df) == 0:
            continue
        rows = []
        for _, r in df.iterrows():
            seat = str(r.get("交易营业部名称", "")).strip()
            reason = str(r.get("类型", "")).strip()
            if not seat:
                continue
            rows.append((date_str, code, seat,
                         _jsonable(r.get("买入金额")), _jsonable(r.get("卖出金额")),
                         _jsonable(r.get("净额")), reason))
        if rows:
            conn.executemany("INSERT OR REPLACE INTO seat_daily(date,code,seat,buy_amt,sell_amt,net,reason)"
                             " VALUES (?,?,?,?,?,?,?)", rows)
            n_ok += 1
        time.sleep(0.15)
    conn.commit()
    print(f"[OK] 席位明细 {n_ok}/{len(codes)} 只", flush=True)


def main():
    ap = argparse.ArgumentParser(description="A股行情看板 P0 数据采集器")
    ap.add_argument("--date", default=date.today().strftime("%Y%m%d"), help="YYYYMMDD")
    ap.add_argument("--force", action="store_true", help="强制重采（覆盖当日已有数据）")
    args = ap.parse_args()
    date_str = args.date
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn()
    cal = load_trade_cal(conn)

    if date_str not in cal:
        print(f"[跳过] {date_str} 非交易日")
        conn.close()
        return

    # P4 数据：指数 + 候选池 K 线（独立于日志，每日增量更新）
    fetch_idx_daily(conn, now)
    fetch_kline(conn, date_str, now)

    # P5 数据：价值候选池（估值 + 财务，独立增量）
    fetch_value(conn, date_str, now)
    fetch_news(conn, date_str, now)

    if not args.force and conn.execute(
        "SELECT 1 FROM collect_log WHERE date=? AND status='ok'", (date_str,)
    ).fetchone():
        print(f"[跳过] {date_str} 已有成功记录（--force 可重采）")
        conn.close()
        return

    print(f"[开始] 采集 {date_str} 盘后数据 ...")
    snapshot = {"date": date_str, "collected_at": now, "pools": {}, "breadth": None}

    # 1) 三类股票池
    for kind, (_, label) in POOLS.items():
        rows, n = fetch_pool(kind, date_str)
        if rows is None:
            print(f"[失败] {label} 获取失败")
            snapshot["pools"][kind] = []
            continue
        conn.executemany(
            "INSERT OR REPLACE INTO pool_daily(date, pool_type, code, name, data_json, collected_at)"
            " VALUES (?,?,?,?,?,?)",
            [(date_str, kind, code, name, json.dumps(item, ensure_ascii=False), now)
             for code, name, item in rows],
        )
        snapshot["pools"][kind] = [item for _, _, item in rows]
        print(f"[OK] {label} {n} 只")

    # 2) 市场广度（三级降级，历史日乐咕仅最新会跳过，失败不阻塞主流程）
    b = calc_breadth(target_date=date_str)
    if b:
        if "limit_up" not in b:  # 快照源无涨跌停口径时用池子计数
            b["limit_up"] = len(snapshot["pools"].get("zt", []))
            b["limit_down"] = len(snapshot["pools"].get("dt", []))
        conn.execute(
            "INSERT OR REPLACE INTO breadth(date, up, down, flat, limit_up, limit_down, total, activity, data_json, collected_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (date_str, b["up"], b["down"], b["flat"], b["limit_up"], b["limit_down"], b["total"],
             b.get("activity", ""), json.dumps(b.get("raw", {}), ensure_ascii=False), now),
        )
        snapshot["breadth"] = b
        print(f"[OK] 广度 涨{b['up']} 跌{b['down']} 平{b['flat']} 涨停{b['limit_up']} 跌停{b['limit_down']}")

    # 3) 快照停用：board.db 为唯一数据源，不再生成 snapshot JSON（冗余，避免本地文件堆积）

    # 4) P3 扩展数据：龙虎榜 / 板块资金流 / 昨日涨停跟踪
    fetch_lhb(conn, date_str, now)
    fetch_fund_flow(conn, date_str, now)
    fetch_prev_zt(conn, date_str, now)

    # 5) P6-A 席位明细（依赖龙虎榜已采集）
    fetch_seats(conn, date_str, now)

    # 5) 日志
    conn.execute(
        "INSERT OR REPLACE INTO collect_log(date, status, collected_at) VALUES (?,?,?)",
        (date_str, "ok", now),
    )
    conn.commit()
    conn.close()
    print(f"[完成] {date_str} 采集入库")


if __name__ == "__main__":
    main()
