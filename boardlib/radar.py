#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P19 资讯雷达：纯 RSS 并发聚合（零 key、零第三方依赖）。

源清单：rss_sources.json，移植自 simonlin1212/Vibe-Astock
`datasources/rss_sources.json`（上游策展自 investment-news，106 源 / 12 赛道）。
只做「抓取 → 解析 → 红线过滤 → 时效过滤 → 赛道归类 → 去重排序」，
不碰 SQLite / akshare，便于单测与独立调用。

设计约束（沿用 ashare_board 血泪经验）：
- 每个请求短超时 + 线程池并发，绝不允许单源无响应挂死每日 21:30 自动化；
- 失败只记状态不抛错，消息面失败不能拖垮盘后行情采集；
- 上游清单保持原样，本项目专属参数（超时/条数上限）写在代码里，方便日后对账。
"""
import concurrent.futures
import hashlib
import io
import json
import os
import re
import ssl
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_PATH = os.path.join(BASE, "rss_sources.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
CST = timezone(timedelta(hours=8))

# 国内环境实测（2026-11-07）：106 源中 69 可达，慢源约 8-25s；
# 6s 硬上限 + 48 线程把整轮压到 ~30s，同时保留绝大多数可用源。
HARD_TIMEOUT = 6
DEFAULT_WORKERS = 48
MAX_BYTES = 1_200_000     # 单源 body 硬上限
CHUNK = 65536             # 分块读：凑够条目即停，不把 2MB 大 feed 全拉完
TOTAL_TIMEOUT = 60        # 整轮硬上限（由 _collect.py 的线程看门狗兜底）
DEFAULT_PER_SOURCE = 6
DEFAULT_RECENT_DAYS = 7
DEFAULT_MAX_ITEMS = 240


def load_sources(path=None):
    with io.open(path or SOURCES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _child(el, *names):
    for c in el:
        if _local(c.tag) in names:
            return c
    return None


def _text(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def parse_time(s):
    """RFC822 / ISO8601 / 常见中文格式 → 北京时间 wall-clock datetime（naive）。"""
    s = (s or "").strip()
    if not s:
        return None
    dt = None
    try:
        dt = parsedate_to_datetime(s)
    except Exception:
        pass
    if dt is None:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            pass
    if dt is None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                    "%Y/%m/%d %H:%M:%S"):
            try:
                dt = datetime.strptime(s[:19], fmt)
                break
            except ValueError:
                continue
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CST).replace(tzinfo=None)


def _repair_xml(raw):
    """body 被截断时，退到最后一个完整 </item>/</entry> 再补闭合标签。
    实测华尔街见闻/机器之心/新智元/OpenAI 的 feed 都 >300KB，硬截断会让整源归零。
    Atom 需补 </feed>，RSS 需补 </channel></rss>，补错会解析失败。"""
    head = raw[:2000].lower()
    tail = b"</feed>" if (b"<feed" in head and b"<channel" not in head) else b"</channel></rss>"
    for close in (b"</item>", b"</entry>"):
        i = raw.lower().rfind(close)
        if i > 0:
            return raw[:i + len(close)] + tail
    return raw


def _read_until_items(resp, need, deadline, cap=MAX_BYTES):
    """分块读，凑够 need 个完整条目即停；单源墙钟到点也停。
    避免为大 feed 全文（含内联 HTML）耗掉几分钟。"""
    buf = bytearray()
    low_close = (b"</item>", b"</entry>")
    while len(buf) < cap and time.time() < deadline:
        try:
            chunk = resp.read(CHUNK)
        except Exception:
            break
        if not chunk:
            break
        buf.extend(chunk)
        low = bytes(buf).lower()
        if sum(low.count(c) for c in low_close) >= need:
            break
    return bytes(buf)


def _lang(text):
    return "zh" if any("\u4e00" <= c <= "\u9fff" for c in (text or "")) else "en"


def parse_feed(raw, source, track, track_name, per_source=DEFAULT_PER_SOURCE):
    """RSS 2.0 / Atom 通用解析；返回原始条目（尚未做红线与时效过滤）。"""
    try:
        root = ET.fromstring(raw)
    except Exception:
        root = None
    if root is None:
        try:
            root = ET.fromstring(_repair_xml(raw))
        except Exception:
            return []
    out = []
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        title = _text(_child(node, "title"))
        if not title:
            continue
        link = ""
        link_el = _child(node, "link")
        if link_el is not None:
            link = (link_el.get("href") or _text(link_el)).strip()
        if not link:  # Atom 常见多个 <link rel=... href=.../>
            for c in node:
                if _local(c.tag) == "link" and c.get("href"):
                    link = c.get("href").strip()
                    break
        desc = _child(node, "description", "summary", "content", "encoded")
        summary = re.sub(r"<[^>]+>", " ", _text(desc))
        summary = re.sub(r"\s+", " ", summary).strip()
        pub = parse_time(_text(_child(node, "pubdate", "published", "updated", "date", "created")))
        out.append({
            "pub_dt": pub,
            "title": title[:160],
            "summary": summary[:180],
            "link": link[:300],
            "source": source,
            "track": track,
            "track_name": track_name,
        })
        if len(out) >= per_source * 4:
            break
    return out


def is_redline(text, keywords):
    t = (text or "").lower()
    return any(str(k).lower() in t for k in (keywords or []))


def _fetch_one(src, track_names, timeout, per_source, ctx):
    t0 = time.time()
    track = src.get("hint") or "other"
    st = {"source": src.get("name", ""), "track": track,
          "track_name": track_names.get(track, "其他"),
          "ok": False, "count": 0, "err": "", "ms": 0}
    req = urllib.request.Request(src.get("url", ""), headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*",
        "Accept-Encoding": "identity",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = _read_until_items(r, per_source * 2, t0 + timeout)
        items = parse_feed(raw, st["source"], track, st["track_name"], per_source)
        if not items:
            st["err"] = "无条目或解析失败"
        else:
            st["ok"] = True
    except Exception as e:  # noqa: BLE001 - 单源失败必须静默降级
        items = []
        st["err"] = str(e)[:120]
    st["ms"] = int((time.time() - t0) * 1000)
    st["_items"] = items
    return st


def fetch_all(cfg=None, timeout=None, workers=DEFAULT_WORKERS,
              per_source=DEFAULT_PER_SOURCE, recent_days=DEFAULT_RECENT_DAYS,
              max_items=DEFAULT_MAX_ITEMS, sources=None, now=None):
    """并发抓全部源 → (条目 list, 源状态 list)。任何单源失败都不影响其它源。"""
    cfg = cfg or load_sources()
    timeout = min(HARD_TIMEOUT, float(timeout or (cfg.get("fetch") or {}).get("timeout", HARD_TIMEOUT)))
    per_source = int((cfg.get("fetch") or {}).get("per_source", per_source))
    recent_days = int((cfg.get("fetch") or {}).get("recent_days", recent_days))
    track_names = {i["key"]: i["name"] for i in cfg.get("industries", [])}
    keywords = cfg.get("redline_keywords", [])
    srcs = sources if sources is not None else cfg.get("sources", [])
    ctx = ssl.create_default_context()
    wall_now = now or datetime.now(CST).replace(tzinfo=None)
    cutoff = wall_now - timedelta(days=recent_days)
    future = wall_now + timedelta(days=1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_fetch_one, s, track_names, timeout, per_source, ctx)
                for s in srcs]
        raw_status = [f.result() for f in futs]

    seen, pool = set(), []
    for st in raw_status:
        picked = []
        for it in st["_items"]:
            dt = it["pub_dt"]
            if dt is None or dt < cutoff or dt > future:
                continue
            text = it["title"] + " " + it["summary"]
            if is_redline(text, keywords):
                continue
            key = hashlib.md5((it["title"] + "|" + it["link"]).encode("utf-8")).hexdigest()[:16]
            if key in seen:
                continue
            seen.add(key)
            picked.append(it)
            if len(picked) >= per_source:
                break
        st["count"] = len(picked)
        st.pop("_items", None)
        for it in picked:
            pool.append({
                "id": hashlib.md5((it["title"] + "|" + it["link"]).encode("utf-8")).hexdigest()[:16],
                "pub_time": it["pub_dt"].strftime("%Y-%m-%d %H:%M"),
                "title": it["title"], "summary": it["summary"], "link": it["link"],
                "source": it["source"], "track": it["track"], "track_name": it["track_name"],
                "lang": _lang(it["title"]),
            })
    pool.sort(key=lambda x: x["pub_time"], reverse=True)

    # 赛道保底配额：更新慢的赛道（机器人/航天等）不能被全局时间倒序挤光。
    # 每赛道先留 quota 条，剩余名额再按时间补足，总数仍受 max_items 约束。
    by_track = {}
    for it in pool:
        by_track.setdefault(it["track"], []).append(it)
    quota = max(4, max_items // (max(1, len(track_names)) * 2))
    guaranteed = []
    for k in track_names:
        guaranteed.extend(by_track.get(k, [])[:quota])
    gid = {x["id"] for x in guaranteed}
    rest = [x for x in pool if x["id"] not in gid]
    result = guaranteed + rest[:max(0, max_items - len(guaranteed))]
    result.sort(key=lambda x: x["pub_time"], reverse=True)
    return result, raw_status


def track_list(cfg=None):
    cfg = cfg or load_sources()
    return [{"key": i["key"], "name": i["name"]} for i in cfg.get("industries", [])]
